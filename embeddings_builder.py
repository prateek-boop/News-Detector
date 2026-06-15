"""
embeddings_builder.py  —  Production-Grade Embedding & Indexing Pipeline
=========================================================================
Converts raw data sources (PDF, FAQ JSON, CSV catalog, URLs) into a
FAISS vector index + metadata JSON for the F.R.I.D.A.Y. RAG pipeline.

Usage
-----
    python embeddings_builder.py --config config.yaml
    python embeddings_builder.py --pdf data/report.pdf --run-id v2
    python embeddings_builder.py --help

Environment Variables
---------------------
    EMBED_MODEL        SentenceTransformer model name   (default: all-MiniLM-L6-v2)
    CHUNK_SIZE         Words per chunk                  (default: 400)
    CHUNK_OVERLAP      Word overlap between chunks      (default: 80)
    OUTPUT_DIR         Directory for index + metadata   (default: ./index_store)
    LOG_LEVEL          DEBUG | INFO | WARNING | ERROR   (default: INFO)
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import os
import re
import sys
import time
import traceback
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Generator

import faiss
import numpy as np
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

# ─────────────────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────────────────

def _setup_logging(level: str = "INFO") -> logging.Logger:
    fmt = "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s"
    logging.basicConfig(format=fmt, datefmt="%Y-%m-%d %H:%M:%S", level=level.upper())
    return logging.getLogger("friday.embeddings")


log = _setup_logging(os.environ.get("LOG_LEVEL", "INFO"))


# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM EXCEPTIONS
# ─────────────────────────────────────────────────────────────────────────────

class EmbeddingPipelineError(RuntimeError):
    """Base error for this module."""

class LoaderError(EmbeddingPipelineError):
    """Raised when a data source cannot be loaded."""

class IndexBuildError(EmbeddingPipelineError):
    """Raised when FAISS index construction fails."""

class ConfigError(EmbeddingPipelineError):
    """Raised for invalid configuration."""


# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PipelineConfig:
    """All runtime settings — overridable via env vars, YAML, or CLI."""

    # Model
    embed_model: str = field(
        default_factory=lambda: os.environ.get("EMBED_MODEL", "all-MiniLM-L6-v2")
    )

    # Chunking
    chunk_size:    int = field(default_factory=lambda: int(os.environ.get("CHUNK_SIZE",    "400")))
    chunk_overlap: int = field(default_factory=lambda: int(os.environ.get("CHUNK_OVERLAP", "80")))
    min_chunk_len: int = 50     # chars — shorter chunks discarded

    # Embedding
    batch_size: int = 32

    # Output
    output_dir: Path = field(
        default_factory=lambda: Path(os.environ.get("OUTPUT_DIR", "./index_store"))
    )
    run_id: str = ""            # appended to file names, e.g. "v2"

    # Sources — populated at runtime
    pdfs:     list[str] = field(default_factory=list)
    faqs:     list[str] = field(default_factory=list)
    catalogs: list[str] = field(default_factory=list)
    urls:     list[str] = field(default_factory=list)

    # Incremental mode: skip sources whose hash hasn't changed
    incremental: bool = True

    def validate(self) -> None:
        if self.chunk_overlap >= self.chunk_size:
            raise ConfigError(
                f"chunk_overlap ({self.chunk_overlap}) must be < chunk_size ({self.chunk_size})"
            )
        if self.batch_size < 1:
            raise ConfigError("batch_size must be ≥ 1")

    @property
    def index_path(self) -> Path:
        suffix = f"_{self.run_id}" if self.run_id else ""
        return self.output_dir / f"pdf_index{suffix}.faiss"

    @property
    def chunks_path(self) -> Path:
        suffix = f"_{self.run_id}" if self.run_id else ""
        return self.output_dir / f"pdf_chunks{suffix}.json"

    @property
    def embeddings_path(self) -> Path:
        suffix = f"_{self.run_id}" if self.run_id else ""
        return self.output_dir / f"embeddings{suffix}.npy"

    @property
    def hash_cache_path(self) -> Path:
        return self.output_dir / "source_hashes.json"

    @classmethod
    def from_yaml(cls, path: str) -> "PipelineConfig":
        try:
            import yaml  # optional dependency
            with open(path) as f:
                data = yaml.safe_load(f)
            obj = cls()
            for k, v in data.items():
                if hasattr(obj, k):
                    setattr(obj, k, v)
            return obj
        except ImportError:
            raise ConfigError("PyYAML is required for --config. Install with: pip install pyyaml")
        except FileNotFoundError:
            raise ConfigError(f"Config file not found: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# METRICS
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RunMetrics:
    sources_processed: int = 0
    sources_skipped:   int = 0
    sources_failed:    int = 0
    total_chunks:      int = 0
    embed_time_s:      float = 0.0
    index_time_s:      float = 0.0
    total_time_s:      float = 0.0

    def report(self) -> None:
        log.info("─" * 60)
        log.info("Run Metrics")
        log.info("  Sources processed : %d", self.sources_processed)
        log.info("  Sources skipped   : %d (incremental / no change)", self.sources_skipped)
        log.info("  Sources failed    : %d", self.sources_failed)
        log.info("  Total chunks      : %d", self.total_chunks)
        log.info("  Embed time        : %.1f s", self.embed_time_s)
        log.info("  Index time        : %.1f s", self.index_time_s)
        log.info("  Total time        : %.1f s", self.total_time_s)
        log.info("─" * 60)


# ─────────────────────────────────────────────────────────────────────────────
# INCREMENTAL HASH CACHE
# ─────────────────────────────────────────────────────────────────────────────

def _file_md5(path: str, chunk_bytes: int = 65536) -> str:
    """Fast MD5 of a file — used for incremental change detection."""
    h = hashlib.md5()
    try:
        with open(path, "rb") as f:
            while block := f.read(chunk_bytes):
                h.update(block)
    except OSError:
        return ""
    return h.hexdigest()


def _url_hash(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


class HashCache:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._cache: dict[str, str] = {}
        if path.exists():
            try:
                self._cache = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                log.warning("Hash cache corrupted — rebuilding from scratch.")

    def is_unchanged(self, key: str, current_hash: str) -> bool:
        return self._cache.get(key) == current_hash

    def update(self, key: str, current_hash: str) -> None:
        self._cache[key] = current_hash

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._cache, indent=2), encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# LOADERS
# ─────────────────────────────────────────────────────────────────────────────

def _load_pdf(path: str) -> str:
    try:
        reader = PdfReader(path)
        pages = [p.extract_text() for p in reader.pages if p.extract_text()]
        if not pages:
            raise LoaderError(f"No extractable text in PDF: {path}")
        return "\n".join(pages)
    except Exception as exc:
        raise LoaderError(f"PDF load failed [{path}]: {exc}") from exc


def _load_faq(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as f:
            faqs = json.load(f)
        if not isinstance(faqs, list):
            raise LoaderError(f"FAQ JSON must be a list of {{question, answer}} objects: {path}")
        blocks = [
            f"Q: {item['question'].strip()}\nA: {item['answer'].strip()}"
            for item in faqs
            if item.get("question") and item.get("answer")
        ]
        return "\n\n".join(blocks)
    except (json.JSONDecodeError, KeyError) as exc:
        raise LoaderError(f"FAQ JSON parse failed [{path}]: {exc}") from exc


def _load_catalog(path: str) -> str:
    try:
        rows = []
        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                line = " | ".join(f"{k}: {v}" for k, v in row.items() if v and str(v).strip())
                if line:
                    rows.append(line)
        if not rows:
            raise LoaderError(f"CSV catalog produced no rows: {path}")
        return "\n".join(rows)
    except Exception as exc:
        raise LoaderError(f"CSV load failed [{path}]: {exc}") from exc


def _scrape_url(url: str, timeout: int = 15, retries: int = 3) -> str:
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        raise LoaderError("requests and beautifulsoup4 are required for URL scraping.")

    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, timeout=timeout, headers={"User-Agent": "F.R.I.D.A.Y./1.0"})
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "head", "noscript"]):
                tag.decompose()
            text = soup.get_text(separator=" ")
            if not text.strip():
                raise LoaderError(f"URL returned empty content: {url}")
            return text
        except Exception as exc:
            last_exc = exc
            if attempt < retries:
                wait = 2 ** attempt
                log.warning("URL fetch attempt %d/%d failed (%s) — retrying in %ds", attempt, retries, exc, wait)
                time.sleep(wait)

    raise LoaderError(f"URL scrape failed after {retries} attempts [{url}]: {last_exc}") from last_exc


# ─────────────────────────────────────────────────────────────────────────────
# CLEANING
# ─────────────────────────────────────────────────────────────────────────────

_RE_NON_ASCII  = re.compile(r"[^\x00-\x7F]+")
_RE_LONE_DIGIT = re.compile(r"(?<!\w)\d+(?!\w)")
_RE_WHITESPACE = re.compile(r"\s+")


def clean_text(text: str) -> str:
    text = _RE_NON_ASCII.sub(" ", text)
    text = _RE_LONE_DIGIT.sub(" ", text)
    text = _RE_WHITESPACE.sub(" ", text)
    return text.strip()


# ─────────────────────────────────────────────────────────────────────────────
# CHUNKING  (overlapping word windows)
# ─────────────────────────────────────────────────────────────────────────────

def chunk_text(
    text: str,
    source: str,
    source_type: str,
    cfg: PipelineConfig,
) -> list[dict]:
    """
    Split text into overlapping word-window chunks.
    The metadata key is "chunk" — this MUST match rag_pipeline.py's retrieve().
    """
    words = text.split()
    if not words:
        return []

    chunks: list[dict] = []
    step = cfg.chunk_size - cfg.chunk_overlap
    if step < 1:
        step = 1

    for chunk_id, i in enumerate(range(0, len(words), step)):
        window = " ".join(words[i : i + cfg.chunk_size])
        if len(window.strip()) < cfg.min_chunk_len:
            continue
        chunks.append({
            "id":          chunk_id,
            "chunk":       window,        # ← key consumed by rag_pipeline.retrieve()
            "source":      source,
            "source_type": source_type,
            "word_start":  i,
            "word_end":    min(i + cfg.chunk_size, len(words)),
        })

    return chunks


# ─────────────────────────────────────────────────────────────────────────────
# EMBEDDING  (L2-normalised for cosine / IndexFlatIP)
# ─────────────────────────────────────────────────────────────────────────────

def embed_chunks(
    chunks: list[dict],
    model: SentenceTransformer,
    cfg: PipelineConfig,
) -> np.ndarray:
    texts = [c["chunk"] for c in chunks]
    log.info("Embedding %d chunks (batch=%d) …", len(texts), cfg.batch_size)

    t0 = time.perf_counter()
    embeddings = model.encode(
        texts,
        batch_size=cfg.batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
    ).astype("float32")
    elapsed = time.perf_counter() - t0

    faiss.normalize_L2(embeddings)      # ← required for cosine sim via IndexFlatIP
    log.info("Embedding complete in %.1f s  (%.0f chunks/s)", elapsed, len(texts) / elapsed)
    return embeddings, elapsed


# ─────────────────────────────────────────────────────────────────────────────
# INDEX
# ─────────────────────────────────────────────────────────────────────────────

def build_index(embeddings: np.ndarray) -> tuple[faiss.Index, float]:
    dim = embeddings.shape[1]
    log.info("Building IndexFlatIP (dim=%d, vectors=%d) …", dim, len(embeddings))
    t0 = time.perf_counter()
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    elapsed = time.perf_counter() - t0
    log.info("Index built in %.2f s", elapsed)
    return index, elapsed


# ─────────────────────────────────────────────────────────────────────────────
# PERSISTENCE
# ─────────────────────────────────────────────────────────────────────────────

def save_outputs(
    index: faiss.Index,
    chunks: list[dict],
    embeddings: np.ndarray,
    cfg: PipelineConfig,
) -> None:
    cfg.output_dir.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, str(cfg.index_path))
    log.info("FAISS index    → %s", cfg.index_path)

    cfg.chunks_path.write_text(
        json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log.info("Chunk metadata → %s", cfg.chunks_path)

    np.save(str(cfg.embeddings_path), embeddings)
    log.info("Embeddings     → %s", cfg.embeddings_path)


# ─────────────────────────────────────────────────────────────────────────────
# SMOKE TEST
# ─────────────────────────────────────────────────────────────────────────────

def smoke_test(
    index: faiss.Index,
    chunks: list[dict],
    model: SentenceTransformer,
    query: str = "What are the key skills for data engineering?",
    top_k: int = 3,
) -> None:
    log.info("── Smoke test ──────────────────────────────────────")
    log.info("Query: %s", query)
    q_vec = model.encode([query]).astype("float32")
    faiss.normalize_L2(q_vec)
    scores, indices = index.search(q_vec, top_k)
    for rank, (score, idx) in enumerate(zip(scores[0], indices[0]), 1):
        if 0 <= idx < len(chunks):
            preview = chunks[idx]["chunk"][:100].replace("\n", " ")
            log.info("  [%d] score=%.4f  %s …", rank, score, preview)
    log.info("────────────────────────────────────────────────────")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

def run_pipeline(cfg: PipelineConfig) -> RunMetrics:
    cfg.validate()
    cfg.output_dir.mkdir(parents=True, exist_ok=True)

    metrics    = RunMetrics()
    hash_cache = HashCache(cfg.hash_cache_path) if cfg.incremental else None
    t_total    = time.perf_counter()

    # ── Load model ───────────────────────────────────────────────
    log.info("Loading embedding model: %s", cfg.embed_model)
    try:
        model = SentenceTransformer(cfg.embed_model)
    except Exception as exc:
        raise EmbeddingPipelineError(f"Cannot load embedding model '{cfg.embed_model}': {exc}") from exc

    # ── Ingest all sources ───────────────────────────────────────
    log.info("Ingesting sources …")
    all_chunks: list[dict] = []

    source_list: list[tuple[str, str]] = (
        [("pdf", p) for p in cfg.pdfs]
        + [("faq", p) for p in cfg.faqs]
        + [("catalog", p) for p in cfg.catalogs]
        + [("url", u) for u in cfg.urls]
    )

    if not source_list:
        raise ConfigError("No data sources specified. Use --pdf, --faq, --catalog, or --url.")

    for source_type, path in source_list:
        current_hash = _file_md5(path) if source_type != "url" else _url_hash(path)

        if hash_cache and hash_cache.is_unchanged(path, current_hash):
            log.info("  SKIP  [%s]  %s  (unchanged since last run)", source_type.upper(), path)
            metrics.sources_skipped += 1
            continue

        log.info("  LOAD  [%s]  %s", source_type.upper(), path)
        try:
            if source_type == "pdf":
                raw = _load_pdf(path)
            elif source_type == "faq":
                raw = _load_faq(path)
            elif source_type == "catalog":
                raw = _load_catalog(path)
            elif source_type == "url":
                raw = _scrape_url(path)
            else:
                log.warning("Unknown source type '%s' — skipping.", source_type)
                metrics.sources_failed += 1
                continue

            cleaned = clean_text(raw)
            chunks  = chunk_text(cleaned, source=path, source_type=source_type, cfg=cfg)
            log.info("  → %d chunks created", len(chunks))
            all_chunks.extend(chunks)
            metrics.sources_processed += 1

            if hash_cache:
                hash_cache.update(path, current_hash)

        except LoaderError as exc:
            log.error("  FAIL  %s", exc)
            metrics.sources_failed += 1

    if not all_chunks:
        if metrics.sources_skipped > 0:
            log.info("All sources skipped (unchanged). No new chunks to process.")
            metrics.total_time_s = time.perf_counter() - t_total
            return metrics
        
        raise EmbeddingPipelineError(
            "No chunks were produced. Check your source files and paths."
        )

    log.info("Total chunks across all sources: %d", len(all_chunks))
    metrics.total_chunks = len(all_chunks)

    # ── Embed ────────────────────────────────────────────────────
    embeddings, embed_time = embed_chunks(all_chunks, model, cfg)
    metrics.embed_time_s = embed_time

    # ── Build index ──────────────────────────────────────────────
    index, index_time = build_index(embeddings)
    metrics.index_time_s = index_time

    # ── Persist ──────────────────────────────────────────────────
    save_outputs(index, all_chunks, embeddings, cfg)

    if hash_cache:
        hash_cache.save()

    # ── Smoke test ───────────────────────────────────────────────
    smoke_test(index, all_chunks, model)

    metrics.total_time_s = time.perf_counter() - t_total
    return metrics


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="embeddings_builder",
        description="Build a FAISS embedding index from multiple data sources.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--config",   metavar="FILE",  help="YAML config file (overrides all flags)")
    p.add_argument("--pdf",      metavar="FILE",  action="append", default=[], dest="pdfs",     help="PDF file(s) to ingest")
    p.add_argument("--faq",      metavar="FILE",  action="append", default=[], dest="faqs",     help="FAQ JSON file(s)")
    p.add_argument("--catalog",  metavar="FILE",  action="append", default=[], dest="catalogs", help="Product catalog CSV(s)")
    p.add_argument("--url",      metavar="URL",   action="append", default=[], dest="urls",     help="URL(s) to scrape")
    p.add_argument("--run-id",   metavar="ID",    default="",                                   help="Suffix for output file names (e.g. v2)")
    p.add_argument("--output-dir", metavar="DIR", default="./index_store",                      help="Output directory (default: ./index_store)")
    p.add_argument("--model",    metavar="NAME",  default=None,                                 help="SentenceTransformer model name")
    p.add_argument("--chunk-size",    type=int, default=None)
    p.add_argument("--chunk-overlap", type=int, default=None)
    p.add_argument("--no-incremental", action="store_true",  help="Re-process all sources even if unchanged")
    p.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args   = parser.parse_args(argv)

    # Re-configure logging with chosen level
    global log
    log = _setup_logging(args.log_level)

    try:
        if args.config:
            cfg = PipelineConfig.from_yaml(args.config)
        else:
            cfg = PipelineConfig()

        # CLI flags override config file / env vars
        if args.pdfs:       cfg.pdfs      = args.pdfs
        if args.faqs:       cfg.faqs      = args.faqs
        if args.catalogs:   cfg.catalogs  = args.catalogs
        if args.urls:       cfg.urls      = args.urls
        if args.run_id:     cfg.run_id    = args.run_id
        if args.output_dir: cfg.output_dir = Path(args.output_dir)
        if args.model:      cfg.embed_model = args.model
        if args.chunk_size:    cfg.chunk_size    = args.chunk_size
        if args.chunk_overlap: cfg.chunk_overlap = args.chunk_overlap
        if args.no_incremental: cfg.incremental  = False

        log.info("=" * 60)
        log.info("F.R.I.D.A.Y. Embeddings Builder")
        log.info("  model      : %s", cfg.embed_model)
        log.info("  chunk_size : %d  overlap: %d", cfg.chunk_size, cfg.chunk_overlap)
        log.info("  output_dir : %s", cfg.output_dir)
        log.info("  run_id     : %s", cfg.run_id or "(none)")
        log.info("  incremental: %s", cfg.incremental)
        log.info("=" * 60)

        metrics = run_pipeline(cfg)
        metrics.report()

        log.info("✅  Build complete.")
        return 0

    except ConfigError as exc:
        log.error("Configuration error: %s", exc)
        return 2
    except EmbeddingPipelineError as exc:
        log.error("Pipeline error: %s", exc)
        return 1
    except KeyboardInterrupt:
        log.warning("Interrupted by user.")
        return 130
    except Exception:
        log.critical("Unexpected error:\n%s", traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
