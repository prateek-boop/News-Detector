"""
rag_pipeline.py  —  F.R.I.D.A.Y.: AI News Authenticator
=========================================================
Hybrid RAG: FAISS retrieval + Dorking news signals + 
CSV verification records + Gemma-3 LLM answer generation.
"""

from __future__ import annotations

import argparse
import glob
import json
import logging
import os
import re
import signal
import sqlite3
import sys
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import faiss
import numpy as np
import torch
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

# ─────────────────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────────────────

def _setup_logging(level: str = "INFO") -> logging.Logger:
    fmt = "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s"
    logging.basicConfig(format=fmt, datefmt="%Y-%m-%d %H:%M:%S", level=level.upper())
    
    # Silence noisy libraries completely
    for logger_name in ["httpx", "httpcore", "sentence_transformers", "huggingface_hub", "transformers", "urllib3"]:
        logging.getLogger(logger_name).setLevel(logging.CRITICAL)
        
    return logging.getLogger("friday.rag")


log = _setup_logging(os.environ.get("LOG_LEVEL", "INFO"))


# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM EXCEPTIONS
# ─────────────────────────────────────────────────────────────────────────────

class RAGPipelineError(RuntimeError):
    """Base error for this module."""

class ModelLoadError(RAGPipelineError):
    """Raised when a model cannot be loaded."""

class IndexLoadError(RAGPipelineError):
    """Raised when the FAISS index or chunk metadata cannot be loaded."""

class ConfigError(RAGPipelineError):
    """Raised for invalid configuration."""


# ─────────────────────────────────────────────────────────────────────────────
# ENV LOADER
# ─────────────────────────────────────────────────────────────────────────────

def _load_dotenv(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    try:
        with open(path, encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and v and k not in os.environ:
                    os.environ[k] = v
    except OSError:
        pass


_load_dotenv()


# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RAGConfig:
    # Index
    index_dir:   Path  = field(default_factory=lambda: Path(os.environ.get("INDEX_DIR", "./index_store")))

    # Retrieval
    top_k:       int   = field(default_factory=lambda: int(os.environ.get("RAG_TOP_K",       "5")))
    min_score:   float = field(default_factory=lambda: float(os.environ.get("RAG_MIN_SCORE", "0.25")))

    # LLM
    max_new_tokens: int = field(default_factory=lambda: int(os.environ.get("LLM_MAX_TOKENS", "512")))
    quantize_4bit:  bool = field(default_factory=lambda: os.environ.get("QUANTIZE", "4bit").lower() == "4bit")

    # Scrapers
    scrapers_root: Path = field(default_factory=lambda: Path(__file__).parent / "scrapping-main")
    dorking_db:    Path = field(default_factory=lambda: Path(__file__).parent / "scrapping-main" / "dorking" / "db.sqlite3")
    dorking_path:  Path = field(default_factory=lambda: Path(__file__).parent / "scrapping-main" / "dorking" / "results.json")
    
    # Cache
    cache_path:    Path = field(default_factory=lambda: Path(__file__).parent / "index_store" / "query_cache.json")
    
    dorking_top_n:  int = 5

    def validate(self) -> None:
        if self.top_k < 1:
            raise ConfigError("top_k must be ≥ 1")
        if not (0.0 <= self.min_score <= 1.0):
            raise ConfigError("min_score must be in [0.0, 1.0]")
        if self.max_new_tokens < 64:
            raise ConfigError("max_new_tokens must be ≥ 64")


# ─────────────────────────────────────────────────────────────────────────────
# QUERY CACHE
# ─────────────────────────────────────────────────────────────────────────────

class QueryCache:
    """Simple persistent cache for LLM responses to avoid redundant thinking."""
    def __init__(self, path: Path):
        self.path = path
        self.cache: dict[str, dict] = {}
        if self.path.exists():
            try:
                self.cache = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                log.warning("Query cache corrupted. Starting fresh.")

    def get(self, query: str) -> dict | None:
        # Basic normalization for better hits
        key = query.lower().strip().replace("?", "").replace("!", "")
        return self.cache.get(key)

    def set(self, query: str, response: dict):
        key = query.lower().strip().replace("?", "").replace("!", "")
        self.cache[key] = response
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.cache, indent=2), encoding="utf-8")
        except Exception as e:
            log.warning(f"Failed to save query cache: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# SCRAPER BRIDGE (Hybrid Retrieval Engine)
# ─────────────────────────────────────────────────────────────────────────────

class ScraperBridge:
    """Keyword-based search over news and dorking SQLite databases."""

    def __init__(self, cfg: RAGConfig):
        self.cfg = cfg

    def search_dorking(self, query: str) -> list[dict]:
        if not self.cfg.dorking_db.exists(): return []
        try:
            conn = sqlite3.connect(self.cfg.dorking_db)
            cursor = conn.cursor()
            # Filter words to focus on relevant keywords
            words = [f"%{w}%" for w in query.split() if len(w) > 2]
            if not words: return []
            
            # Simple keyword search on snippets and titles from web results
            sql = "SELECT title, url, snippet FROM crawler_crawledlink WHERE " + " OR ".join(["(snippet LIKE ? OR title LIKE ?)"] * len(words))
            params = []
            for w in words: params.extend([w, w])
            
            cursor.execute(sql + f" LIMIT {self.cfg.dorking_top_n}", params)
            results = [{"title": r[0], "url": r[1], "snippet": r[2], "source": "Web (News/Context)"} for r in cursor.fetchall()]
            conn.close()
            return results
        except Exception as e:
            log.warning(f"Web context search failed: {e}")
            return []

    def get_hybrid_context(self, query: str) -> str:
        dorking = self.search_dorking(query)
        
        sections = []
        if dorking:
            sec = "LIVE NEWS SIGNALS (from Web Search):\n" + "\n".join([f"- {r['title']} ({r['url']}): {r['snippet'][:200]}..." for r in dorking])
            sections.append(sec)
        
        return "\n\n".join(sections)



# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM MEMORY CHECK
# ─────────────────────────────────────────────────────────────────────────────

def check_system_memory() -> tuple[str, torch.dtype]:
    """
    Inspect available RAM and select an appropriate model + dtype.
    16 GB+  → gemma-3-4b-it  (better quality)
    <16 GB  → gemma-3-1b-it  (safe on lower-RAM machines)
    """
    try:
        import psutil
        vm = psutil.virtual_memory()
        total_gb = round(vm.total / (1024 ** 3))
        avail_gb = round(vm.available / (1024 ** 3))
        log.info("System RAM — total: %d GB  available: %d GB", total_gb, avail_gb)
    except ImportError:
        log.warning("psutil not installed — cannot detect RAM. Defaulting to 1b model.")
        total_gb = 0

    if total_gb >= 16:
        model_id    = "google/gemma-3-4b-it"
        torch_dtype = torch.float16
        log.info("16 GB+ RAM → using gemma-3-4b-it (float16)")
    else:
        model_id    = "google/gemma-3-1b-it"
        torch_dtype = torch.float16
        log.info("<16 GB RAM → using gemma-3-1b-it (float16)")

    return model_id, torch_dtype


# ─────────────────────────────────────────────────────────────────────────────
# HF AUTH
# ─────────────────────────────────────────────────────────────────────────────

def _hf_login() -> None:
    # Check for token case-insensitively
    token = os.environ.get("HF_TOKEN") or os.environ.get("HF_Token") or os.environ.get("hf_token")
    
    if not token or token == "YOUR_HF_TOKEN_HERE":
        log.warning("HF_TOKEN not found in environment or .env file.")
        return
    try:
        from huggingface_hub import login as hf_login
        hf_login(token=token)
        log.info("Hugging Face login successful.")
    except Exception as exc:
        log.warning("HF login failed: %s", exc)


# ─────────────────────────────────────────────────────────────────────────────
# MODEL LOADING
# ─────────────────────────────────────────────────────────────────────────────

def load_llm(model_id: str, torch_dtype: torch.dtype, cfg: RAGConfig) -> tuple:
    """
    Load tokenizer + LLM with optional 4-bit quantization.
    Falls back gracefully through float16 → CPU float16.
    """
    log.info("Loading tokenizer: %s", model_id)
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=True)
    except Exception as exc:
        raise ModelLoadError(f"Tokenizer load failed for '{model_id}': {exc}") from exc

    def _try_load(kwargs: dict) -> Any:
        return AutoModelForCausalLM.from_pretrained(model_id, **kwargs)

    attempts = []

    if cfg.quantize_4bit and torch.cuda.is_available():
        attempts.append(("4-bit quantized (CUDA)", dict(
            quantization_config=BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            ),
            device_map="auto",
            trust_remote_code=True,
        )))

    if torch.cuda.is_available():
        attempts.append(("float16 (CUDA)", dict(
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True,
            device_map="cuda",
        )))

    attempts.append(("float16 (CPU fallback)", dict(
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True,
        device_map="cpu",
    )))

    for label, kwargs in attempts:
        try:
            log.info("Attempting model load: %s …", label)
            llm = _try_load(kwargs)
            log.info("Model loaded via: %s", label)
            return tokenizer, llm
        except Exception as exc:
            log.warning("%s load failed: %s — trying next option.", label, exc)

    raise ModelLoadError(
        f"All load strategies failed for '{model_id}'. "
        "Check HF_TOKEN, internet access, and available RAM."
    )


def load_embedding_model() -> SentenceTransformer:
    model_name = "all-MiniLM-L6-v2"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    log.info("Loading embedding model: %s on %s", model_name, device)
    try:
        return SentenceTransformer(model_name, device=device)
    except Exception as exc:
        raise ModelLoadError(f"Embedding model load failed: {exc}") from exc


# ─────────────────────────────────────────────────────────────────────────────
# INDEX LOADING  (merges multiple FAISS shards)
# ─────────────────────────────────────────────────────────────────────────────

def load_data(index_dir: Path) -> tuple[faiss.Index, BM25Okapi, list[dict]]:
    """
    Auto-discovers all pdf_index*.faiss + pdf_chunks*.json in index_dir,
    merges shards into a single IndexFlatIP (cosine similarity),
    and initializes a BM25 index for keyword search.
    """
    if not index_dir.is_dir():
        raise IndexLoadError(f"Index directory not found: {index_dir}")

    faiss_paths = sorted(index_dir.glob("pdf_index*.faiss"))
    json_paths  = sorted(index_dir.glob("pdf_chunks*.json"))

    if not faiss_paths:
        raise IndexLoadError(f"No pdf_index*.faiss files found in {index_dir}")
    if not json_paths:
        raise IndexLoadError(f"No pdf_chunks*.json files found in {index_dir}")

    all_chunks:  list[dict]        = []
    all_vectors: list[np.ndarray]  = []
    vector_dim:  int | None        = None

    # ── Load JSON metadata ────────────────────────────────────────
    log.info("Loading %d JSON metadata shard(s) …", len(json_paths))
    for path in json_paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            all_chunks.extend(data)
            log.info("  ✓  %5d chunks  ← %s", len(data), path.name)
        except Exception as exc:
            log.error("  FAIL  %s: %s", path.name, exc)

    # ── Load & reconstruct FAISS vectors ─────────────────────────
    log.info("Loading %d FAISS shard(s) …", len(faiss_paths))
    for path in faiss_paths:
        try:
            shard = faiss.read_index(str(path))
            n, d  = shard.ntotal, shard.d

            if vector_dim is None:
                vector_dim = d
            elif vector_dim != d:
                log.warning("  Dimension mismatch in %s (%d ≠ %d) — skipping.", path.name, d, vector_dim)
                continue

            vecs = np.zeros((n, d), dtype="float32")
            for i in range(n):
                shard.reconstruct(i, vecs[i])

            all_vectors.append(vecs)
            log.info("  ✓  %5d vectors  ← %s", n, path.name)
        except Exception as exc:
            log.error("  FAIL  %s: %s", path.name, exc)

    if not all_vectors or vector_dim is None:
        raise IndexLoadError("No FAISS vectors could be loaded. Re-run embeddings_builder.py.")

    # ── Build unified IndexFlatIP ─────────────────────────────────
    combined = np.vstack(all_vectors).astype("float32")
    faiss.normalize_L2(combined)                   # ← normalise for cosine similarity
    index = faiss.IndexFlatIP(vector_dim)          # ← NOT IndexFlatL2
    index.add(combined)

    # ── Build BM25 index ──────────────────────────────────────────
    log.info("Building BM25 index (keyword search) …")
    tokenized_corpus = [c.get("chunk", "").lower().split() for c in all_chunks]
    bm25 = BM25Okapi(tokenized_corpus)

    log.info("Unified index ready: %d vectors  dim=%d", index.ntotal, vector_dim)
    log.info("Total chunks loaded: %d", len(all_chunks))

    if index.ntotal != len(all_chunks):
        log.warning(
            "Vector count (%d) ≠ chunk count (%d). "
            "Index and JSON files may be from different runs.",
            index.ntotal, len(all_chunks)
        )

    return index, bm25, all_chunks


# ─────────────────────────────────────────────────────────────────────────────
# RETRIEVAL
# ─────────────────────────────────────────────────────────────────────────────

def retrieve(
    query:            str,
    emb_model:        SentenceTransformer,
    index:            faiss.Index,
    bm25:             BM25Okapi,
    pages_and_chunks: list[dict],
    cfg:              RAGConfig,
) -> list[dict]:
    """
    Hybrid Search: Combines Dense (FAISS) and Sparse (BM25) results.
    """
    # 1. Dense Retrieval (FAISS)
    query_vec = emb_model.encode([query]).astype("float32")
    faiss.normalize_L2(query_vec)
    d_scores, d_indices = index.search(query_vec, cfg.top_k)

    # 2. Sparse Retrieval (BM25)
    tokenized_query = query.lower().split()
    s_scores = bm25.get_scores(tokenized_query)
    s_indices = np.argsort(s_scores)[::-1][:cfg.top_k]

    # 3. Hybrid Merge (Union of top results)
    merged_results = {}

    # Add FAISS results
    for score, idx in zip(d_scores[0], d_indices[0]):
        if 0 <= idx < len(pages_and_chunks) and score >= cfg.min_score:
            chunk = pages_and_chunks[idx]
            merged_results[idx] = {**chunk, "_score": float(score), "_type": "dense"}

    # Add BM25 results
    for idx in s_indices:
        score = s_scores[idx]
        if score > 0 and 0 <= idx < len(pages_and_chunks):
            if idx not in merged_results:
                chunk = pages_and_chunks[idx]
                merged_results[idx] = {**chunk, "_score": float(score), "_type": "sparse"}
            else:
                merged_results[idx]["_type"] = "hybrid"

    results = list(merged_results.values())
    log.debug("Hybrid Retrieval: %d unique chunks found.", len(results))
    return results


# ─────────────────────────────────────────────────────────────────────────────
# DORKING BRIDGE
# ─────────────────────────────────────────────────────────────────────────────

_EDU_DOMAINS = [
    "coursera", "udemy", "youtube", "deeplearning", "kaggle",
    "mit", "stanford", "github", "edx", "datacamp", "codecademy",
]


def get_dorking_context(query: str, cfg: RAGConfig) -> tuple[str, list[tuple]]:
    if not cfg.dorking_path.exists():
        return "", []
    try:
        data = json.loads(cfg.dorking_path.read_text(encoding="utf-8"))
    except Exception:
        return "", []

    query_words = set(query.lower().split())
    scored: list[tuple] = []

    for entry in data.get("dork_queries", []):
        overlap = len(query_words & set(entry.get("query", "").lower().split()))
        if overlap == 0:
            continue
        for link in entry.get("links", [])[:cfg.dorking_top_n]:
            title   = link.get("title", "")
            url     = link.get("url", "")
            snippet = link.get("snippet", "")
            if title:
                scored.append((overlap, title, url, snippet))

    scored.sort(key=lambda x: -x[0])
    seen: set[str] = set()
    top_links: list[tuple] = []
    for _, title, url, snippet in scored:
        if url not in seen and len(top_links) < cfg.dorking_top_n:
            seen.add(url)
            top_links.append((title, url, snippet))

    if not top_links:
        return "", []

    lines = [
        f"{i}. {title}" + (f" — {snippet[:120]}" if snippet else "")
        for i, (title, _, snippet) in enumerate(top_links, 1)
    ]
    return "\n".join(lines), top_links


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def format_prompt(query: str, context_items: list[dict], hybrid_context: str = "", history: list[dict] | None = None) -> str:
    """
    Build the RAG prompt for F.R.I.D.A.Y. (News Authenticator).
    Includes conversation history for context-awareness.
    """
    context_str = "\n---\n".join(
        item.get("chunk", "").strip()
        for item in context_items
        if item.get("chunk")
    )
    if not context_str:
        context_str = "No relevant verification data found in the local dataset."

    history_str = ""
    if history:
        history_str = "\nRECENT CONVERSATION:\n" + "\n".join(
            [f"User: {h['user']}\nF.R.I.D.A.Y.: {h['assistant']}" for h in history]
        )

    hybrid_section = (
        f"\n\nLIVE AUTHENTICATION SIGNALS (from web search):\n{hybrid_context}"
        if hybrid_context else ""
    )

    return f"""You are F.R.I.D.A.Y., an expert analytical assistant and news authenticator.
Your goal is to provide clear, human-like analysis grounded strictly in the provided data to determine if news is fake or true.

GUIDELINES FOR BEING THE BEST:
1. Speak like a human expert, not a machine. Use natural transitions.
2. If the user asks a follow-up, look at the RECENT CONVERSATION to understand the context.
3. Combine the "conversational_response" and "overall_explanation" into a single, cohesive narrative.
4. Output ONLY valid JSON.

QUERY: {query}
{history_str}

VERIFICATION EVIDENCE:
{context_str}{hybrid_section}

JSON OUTPUT:
{{
  "conversational_response": "<A friendly, human-like introduction and greeting>",
  "verdict": "<A short label for the finding (e.g., TRUE NEWS, FAKE NEWS, SUMMARY, INSUFFICIENT DATA)>",
  "confidence": 90,
  "key_finding": "<A concise, one-sentence summary of the main insight>",
  "data_points": ["Specific data point 1", "Specific data point 2"],
  "evidence_quote": "<A short direct quote supporting the finding>",
  "overall_explanation": "<A detailed, professional explanation of the context, avoiding robotic language>"
}}"""


# ─────────────────────────────────────────────────────────────────────────────
# LLM GENERATION
# ─────────────────────────────────────────────────────────────────────────────

def generate_answer(
    prompt:    str,
    tokenizer: Any,
    llm:       Any,
    cfg:       RAGConfig,
) -> str:
    """
    Run the LLM. Tokens sent to model's actual device.
    Uses stop sequences to prevent multiple JSON blocks.
    """
    device = next(llm.parameters()).device
    input_ids = tokenizer(prompt, return_tensors="pt").to(device)

    t0 = time.perf_counter()
    with torch.no_grad():
        outputs = llm.generate(
            **input_ids,
            temperature=0.1,  # Slight temperature for better reasoning
            do_sample=True,
            max_new_tokens=cfg.max_new_tokens,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.eos_token_id,
        )
    elapsed = time.perf_counter() - t0
    log.debug("LLM generation: %.1f s", elapsed)

    generated = outputs[0][input_ids["input_ids"].shape[1]:]
    text = tokenizer.decode(generated, skip_special_tokens=True)

    # If the model starts a second JSON block, cut it off
    if text.count("{") > 1:
        parts = text.split("}")
        text = parts[0] + "}"

    return text.strip()


# ─────────────────────────────────────────────────────────────────────────────
# JSON PARSER / CLEANER
# ─────────────────────────────────────────────────────────────────────────────

def clean_and_parse(raw: str) -> dict:
    # Remove markdown fences if present
    text = re.sub(r"```(?:json)?", "", raw).strip()
    
    # Try to find the first valid JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model output.")
    
    json_str = match.group()
    
    # Fix common placeholder hallucinations in 1B models
    json_str = json_str.replace("<0-100>", "50")
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # Final fallback: try to fix common JSON errors (like trailing commas)
        json_str = re.sub(r",\s*}", "}", json_str)
        return json.loads(json_str)


# ─────────────────────────────────────────────────────────────────────────────
# HUMAN-READABLE OUTPUT
# ─────────────────────────────────────────────────────────────────────────────

_VERDICT_ICONS = {
    "HIGH DEMAND":       "🔥",
    "MODERATE DEMAND":   "📈",
    "MIXED TRENDS":      "⚡",
    "LOW DEMAND":        "📉",
    "DECLINING":         "🔻",
    "INSUFFICIENT DATA": "❓",
}


def _wrap(text: str, width: int, indent: str = "    ") -> None:
    words, line = text.split(), ""
    for w in words:
        if len(line) + len(w) + 1 > width:
            print(indent + line)
            line = w
        else:
            line = (line + " " + w).strip()
    if line:
        print(indent + line)


def print_human_output(
    parsed:       dict,
    web_sources:  list[tuple],
    cfg:          RAGConfig,
) -> None:
    intro       = parsed.get("conversational_response", "")
    verdict     = parsed.get("verdict", "UNKNOWN")
    confidence  = int(parsed.get("confidence", 0))
    key         = parsed.get("key_finding", "")
    quote       = parsed.get("evidence_quote", "")
    explanation = parsed.get("overall_explanation", "")

    icon   = _VERDICT_ICONS.get(verdict, "📊")
    filled = confidence // 10
    bar    = "█" * filled + "░" * (10 - filled)

    try:
        W = min(os.get_terminal_size().columns, 80)
    except OSError:
        W = 80

    SEP  = "─" * W
    TSEP = "═" * W

    print(f"\n{TSEP}")
    print("  F.R.I.D.A.Y.  |  AI News Authenticator")
    print(TSEP)
    
    if intro and intro.strip():
        print(f"\n  💬  {intro}")
        print(f"\n{SEP}")

    print(f"  {icon}  VERDICT    :  {verdict}")
    print(f"  📊  CONFIDENCE : {confidence}%  [{bar}]")
    print(SEP)

    if key:
        print("  💡 KEY FINDING")
        _wrap(key, W - 6, "     ")
        print()

    if explanation:
        print("  📝 ANALYSIS")
        _wrap(explanation, W - 6, "     ")
        print()

    if quote and quote.lower() not in ("", "none", "no relevant evidence"):
        print("  📖 EVIDENCE QUOTE")
        _wrap(f'"{quote}"', W - 6, "     ")
        print()

    print(SEP)

    # ── Web references ────────────────────────────────────────────
    if web_sources:
        print("  🌐 REFERENCES  —  Live Web Sources (News Context)")
        print(SEP)
        for i, (title, url, _) in enumerate(web_sources, 1):
            short = (title[:52] + "…") if len(title) > 52 else title
            print(f"  [{i}] {short}")
            print(f"       🔗 {url}")
        print()

    print(TSEP + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# SINGLE-QUERY PROCESSOR
# ─────────────────────────────────────────────────────────────────────────────

def process_query(
    query:            str,
    tokenizer:        Any,
    llm:              Any,
    emb_model:        SentenceTransformer,
    index:            faiss.Index,
    bm25:             BM25Okapi,
    pages_and_chunks: list[dict],
    cfg:              RAGConfig,
    history:          list[dict] | None = None,
    cache:            QueryCache | None = None,
) -> str:
    t0 = time.perf_counter()

    # Step 0: Check Cache
    if cache:
        cached_response = cache.get(query)
        if cached_response:
            log.info("[Cache] Instant hit for: %s", query)
            print_human_output(cached_response, [], cfg)
            final_text = cached_response.get("conversational_response", "") + " " + cached_response.get("overall_explanation", "")
            return final_text.strip()

    # Step 1: Hybrid Retrieval (FAISS + BM25)
    context_items = retrieve(query, emb_model, index, bm25, pages_and_chunks, cfg)
    log.debug("Retrieved %d context chunks.", len(context_items))

    # Step 2: Hybrid Retrieval (Keyword-based from Scrapers)
    bridge = ScraperBridge(cfg)
    hybrid_context = bridge.get_hybrid_context(query)
    
    # Also get web sources for references display
    _, web_sources = get_dorking_context(query, cfg)

    # Step 3: Build prompt
    prompt = format_prompt(query, context_items, hybrid_context=hybrid_context, history=history)

    # Step 4: Generate answer
    answer = generate_answer(prompt, tokenizer, llm, cfg)

    # Step 5: Parse + display
    try:
        parsed = clean_and_parse(answer)
        
        # Save to Cache
        if cache:
            cache.set(query, parsed)
            
        print_human_output(parsed, web_sources, cfg)
        final_text = parsed.get("conversational_response", "") + " " + parsed.get("overall_explanation", "")
        return final_text.strip()
    except Exception as parse_exc:
        log.warning("JSON parse failed (%s) — showing raw output.", parse_exc)
        print("\n--- Raw Model Response ---")
        for ln in answer.splitlines():
            s = ln.strip()
            if s and s not in ("```", "```json"):
                print(" ", s)
        print("--------------------------")
        if web_sources:
            print("\n📌 REFERENCES  (Dorking sources)")
            print("─" * 58)
            for i, (title, url, _) in enumerate(web_sources, 1):
                print(f"  [{i}] {title}")
                print(f"       🔗 {url}")
            print("─" * 58)
        return answer

    log.debug("Query processed in %.1f s", time.perf_counter() - t0)


# ─────────────────────────────────────────────────────────────────────────────
# GRACEFUL SHUTDOWN
# ─────────────────────────────────────────────────────────────────────────────

_shutdown_requested = False

def _handle_signal(sig: int, _frame: Any) -> None:
    global _shutdown_requested
    _shutdown_requested = True
    print("\n\n[Signal received — shutting down after current query …]\n")


def auto_ingest_data(cfg: RAGConfig) -> None:
    """
    Automatically discovery and ingest local PDFs and CSVs into the FAISS index.
    """
    try:
        from embeddings_builder import run_pipeline, PipelineConfig
        
        # Auto-discover files in the root directory
        pdfs = [str(p) for p in Path(".").glob("*.pdf")]
        csvs = [str(p) for p in Path(".").glob("*.csv")]
        
        if not pdfs and not csvs:
            log.info("No local PDF or CSV files found for auto-ingestion.")
            return

        log.info("Checking for new/updated data: %d PDFs, %d CSVs", len(pdfs), len(csvs))
        
        embed_cfg = PipelineConfig(
            pdfs=pdfs,
            catalogs=csvs,
            output_dir=cfg.index_dir,
            incremental=True  # Important: skips files that haven't changed
        )
        
        # Run the ingestion pipeline
        run_pipeline(embed_cfg)
        log.info("Auto-ingestion check complete.")
        
    except ImportError:
        log.warning("embeddings_builder.py not found. Skipping auto-ingestion.")
    except Exception as e:
        log.error("Auto-ingestion failed: %s", e)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────────────────────────────────────

def run_interactive(
    tokenizer:        Any,
    llm:              Any,
    emb_model:        SentenceTransformer,
    index:            faiss.Index,
    bm25:             BM25Okapi,
    pages_and_chunks: list[dict],
    cfg:              RAGConfig,
) -> None:
    try:
        W = min(os.get_terminal_size().columns, 80)
    except OSError:
        W = 80

    print("\n" + "═" * W)
    print(f"  Hybrid RAG · News Verification Signals   v1.1  |  index: {{cfg.index_dir}}")
    print("═" * W)
    print("  Your personal AI News Authenticator.  Commands: exit | quit | /reload")
    print("═" * W + "\n")

    history: list[dict] = []
    cache = QueryCache(cfg.cache_path)

    while not _shutdown_requested:
        try:
            query = input("❯  F.R.I.D.A.Y.: ").strip()
        except EOFError:
            break

        if not query:
            continue
        if query.lower() in ("exit", "quit"):
            break
        if query == "/reload":
            log.info("Reloading index from %s …", cfg.index_dir)
            try:
                new_index, new_bm25, new_chunks = load_data(cfg.index_dir)
                index = new_index
                bm25 = new_bm25
                pages_and_chunks[:] = new_chunks
                log.info("Index reloaded: %d vectors.", index.ntotal)
            except IndexLoadError as exc:
                log.error("Reload failed: %s", exc)
            continue

        print("\n[Thinking …]")
        try:
            answer = process_query(query, tokenizer, llm, emb_model, index, bm25, pages_and_chunks, cfg, history=history, cache=cache)
            # Maintain a short history (last 5 turns)
            history.append({"user": query, "assistant": answer})
            if len(history) > 5:
                history.pop(0)
        except KeyboardInterrupt:
            print("\n[Query interrupted]\n")
        except Exception:
            log.error("Unexpected error during query:\n%s", traceback.format_exc())

    print("\nGoodbye! — F.R.I.D.A.Y. shutting down.\n")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="rag_pipeline",
        description="F.R.I.D.A.Y.: Hybrid RAG AI News Authenticator system.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--index-dir",      metavar="DIR",   default=None,  help="FAISS index directory (default: ./index_store)")
    p.add_argument("--query",          metavar="TEXT",  default=None,  help="Run a single query and exit (non-interactive)")
    p.add_argument("--no-interactive", action="store_true",            help="Alias for piping: exits after --query")
    p.add_argument("--top-k",          type=int,        default=None,  help="Chunks to retrieve per query (default: 5)")
    p.add_argument("--min-score",      type=float,      default=None,  help="Min cosine similarity threshold (default: 0.25)")
    p.add_argument("--max-tokens",     type=int,        default=None,  help="Max LLM output tokens (default: 512)")
    p.add_argument("--no-4bit",        action="store_true",            help="Disable 4-bit quantization")
    p.add_argument("--log-level",      default="INFO",  choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args   = parser.parse_args(argv)

    global log
    log = _setup_logging(args.log_level)

    # Register graceful shutdown signals
    signal.signal(signal.SIGINT,  _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    try:
        cfg = RAGConfig()
        if args.index_dir:  cfg.index_dir      = Path(args.index_dir)
        if args.top_k:      cfg.top_k          = args.top_k
        if args.min_score:  cfg.min_score      = args.min_score
        if args.max_tokens: cfg.max_new_tokens = args.max_tokens
        if args.no_4bit:    cfg.quantize_4bit  = False
        cfg.validate()

        _hf_login()

        log.info("=" * 60)
        log.info("F.R.I.D.A.Y. RAG Pipeline")
        log.info("  index_dir  : %s", cfg.index_dir)
        log.info("  top_k      : %d  min_score: %.2f", cfg.top_k, cfg.min_score)
        log.info("  max_tokens : %d", cfg.max_new_tokens)
        log.info("  4-bit quant: %s", cfg.quantize_4bit)
        log.info("=" * 60)

        # Step 0: Auto-Ingest local data
        auto_ingest_data(cfg)

        # Load index
        index, bm25, pages_and_chunks = load_data(cfg.index_dir)

        # Load models
        model_id, torch_dtype    = check_system_memory()
        tokenizer, llm           = load_llm(model_id, torch_dtype, cfg)
        emb_model                = load_embedding_model()

        # Single-query mode
        if args.query:
            print("\n[Thinking …]")
            cache = QueryCache(cfg.cache_path)
            process_query(args.query, tokenizer, llm, emb_model, index, bm25, pages_and_chunks, cfg, cache=cache)
            return 0

        # Interactive mode
        run_interactive(tokenizer, llm, emb_model, index, bm25, pages_and_chunks, cfg)
        return 0

    except (ConfigError, IndexLoadError, ModelLoadError) as exc:
        log.error("%s", exc)
        return 1
    except KeyboardInterrupt:
        log.warning("Interrupted by user.")
        return 130
    except Exception:
        log.critical("Unexpected error:\n%s", traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
