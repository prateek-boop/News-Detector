# 🤖 F.R.I.D.A.Y. - AI News Authenticator

**F.R.I.D.A.Y.** (Fact-based Retrieval Intelligence with Distributed AI & Verification Year-round) is an advanced **AI-powered News Verification and Fact-Checking System** built using a **Hybrid Retrieval-Augmented Generation (RAG) Architecture** with integrated web scraping capabilities.

The system combines PDF document indexing, CSV-based verification records, BM25 lexical retrieval, semantic vector search, and multi-source web scraping to provide accurate, explainable, and evidence-backed news analysis.

---

## 🚀 Overview

The rapid spread of misinformation across digital platforms makes news verification increasingly challenging. F.R.I.D.A.Y. addresses this by leveraging a **Hybrid RAG Pipeline** that:

* **Indexes documents** (PDFs, structured data) into FAISS vector embeddings
* **Retrieves information** using both BM25 and semantic search
* **Scrapes live data** from multiple web sources (LinkedIn, news sites, etc.)
* **Cross-references claims** against CSV verification datasets
* **Generates responses** using Gemma-3 LLM with evidence backing

The system architecture combines:

* **FAISS vector database** for fast semantic search
* **BM25 lexical retrieval** for keyword matching
* **Hybrid ranking** for merged results
* **Multi-source web scraping** (LinkedIn, Unstop, Dorking)
* **LLM caching** to reduce latency and costs
* **Query caching** for repeated questions

---

## ✨ Features

### 🔍 Hybrid Retrieval System

Combines dual retrieval strategies:

* **BM25 Algorithm**
  * Efficient keyword-based retrieval
  * Excellent lexical matching for exact terms

* **Semantic Search with FAISS**
  * Embedding-based contextual retrieval
  * Finds relevant articles beyond exact keyword matches
  * Fast nearest-neighbor search on large datasets

* **Intelligent Result Merging**
  * Ranks and fuses lexical and semantic results
  * Improves overall retrieval accuracy and relevance

---

### 📚 Document Indexing Pipeline

* **PDF Processing**: Automatically chunks and embeds PDF documents
* **Configurable Chunking**: Adjustable chunk size and overlap for optimal context
* **Metadata Tracking**: Maintains source information and modification hashes
* **Persistent Storage**: FAISS indices cached for quick reloading
* **Multi-format Support**: PDFs, JSON datasets, and CSV records

---

### 🌐 Multi-Source Web Scraping

Integrated scraping tools for:

* **LinkedIn Data**: Contact extraction, profile scraping, email collection
* **Unstop/Devfolio**: Event and hackathon participant tracking
* **Google Dorking**: Advanced search result aggregation
* **Real-time Collection**: Fetches latest information unavailable in static datasets

---

### 🧠 Retrieval-Augmented Generation (RAG)

Reduces hallucinations through evidence-based generation:

1. User query submitted
2. Relevant documents retrieved via FAISS + BM25
3. Context injected into LLM prompt
4. Gemma-3 generates grounded responses
5. Results cached for reuse

---

### ⚡ Intelligent Caching

* **Query Cache**: Stores previous questions and answers
* **Response Memoization**: Reuses LLM outputs for identical queries
* **Reduces Latency**: Faster response times for repeated questions
* **Lower Costs**: Minimizes redundant API calls

---

### 🛡️ Verification & Cross-Reference

The system includes:

* **CSV Verification Records**: Fake.csv and True.csv datasets for fact-checking
* **Multi-source Cross-Reference**: Validates claims across retrieved documents
* **Evidence Tracking**: Shows sources and confidence scores
* **Structured Output**: Structured verification results

---

## 🏗️ Architecture

```text
                     User Query
                          │
                ┌─────────┴─────────┐
                │                   │
                ▼                   ▼
        Web Scraping         Pre-indexed
                             FAISS Index
                │                   │
                └─────────┬─────────┘
                          ▼
              Document Collection
                          │
         ┌────────────────┼────────────────┐
         │                │                │
         ▼                ▼                ▼
      PDF Chunks      CSV Verification  Scraped
      (embeddings)      Records         Content
         │                │                │
         └────────────────┼────────────────┘
                          ▼
           Query Processing & Ranking
                          │
         ┌────────────────┼────────────────┐
         │                │                │
         ▼                ▼                ▼
    BM25 Retrieval   FAISS Search    Dorking
    (Lexical)      (Semantic)       Signals
         │                │                │
         └────────────────┼────────────────┘
                          ▼
                  Hybrid Ranking
                          │
                          ▼
                   Top-K Results
                          │
                          ▼
                   Context Preparation
                          │
                          ▼
                  RAG Prompt Building
                          │
                          ▼
                 Gemma-3 LLM Response
                          │
                          ▼
                   Cache Response
                          │
                          ▼
                  User Response
```

## 🛠️ Tech Stack

### Core Framework
* **Python** 3.8+
* **PyTorch** (torch)
* **Transformers** (Hugging Face)

### Vector Database & Retrieval
* **FAISS** (Facebook AI Similarity Search)
* **BM25Okapi** (rank-bm25)
* **Sentence Transformers** (embedding models)

### Large Language Model
* **Gemma-3** (via Transformers)
* **BitsAndBytes** (4-bit quantization for efficiency)
* **Accelerate** (multi-GPU support)

### Data Processing
* **PyPDF** (PDF reading and chunking)
* **BeautifulSoup4** (web scraping)
* **Selenium** (browser automation for JavaScript-heavy sites)

### Web & Data Collection
* **Requests** (HTTP client)
* **SQLite3** (local data storage)

### Utilities
* **NumPy** (numerical operations)
* **PyYAML** (configuration files)
* **PSUtil** (system monitoring)

---

## 📂 Project Structure

```text
RAG/
│
├── embeddings_builder.py       # Convert PDFs/CSVs → FAISS index + metadata
├── rag_pipeline.py             # Main RAG pipeline: retrieval → LLM → response
├── requirements.txt            # Python dependencies
│
├── Fake.csv                    # Verification dataset (false records)
├── True.csv                    # Verification dataset (true records)
│
├── index_store/                # FAISS indices & cached data
│   ├── pdf_index.faiss         # FAISS vector index
│   ├── embeddings.npy          # Document embeddings
│   ├── pdf_chunks.json         # Chunk metadata & sources
│   ├── query_cache.json        # Query response cache
│   └── source_hashes.json      # Source file hashes for tracking changes
│
└── scrapping-main/             # Multi-source web scraping infrastructure
    ├── linkedin/               # LinkedIn profile & contact scraper
    │   ├── extract_linkedin_emails.py
    │   ├── extract_linkedin_emails_sb.py
    │   └── ... (contact extraction tools)
    │
    ├── unstop_crawler/         # Unstop/Devfolio hackathon scraper
    │   ├── capture_devfolio_api.py
    │   └── ... (event data collection)
    │
    ├── dorking/                # Google Dorking search results aggregator
    │   ├── crawler/
    │   └── dork_crawler/
    │
    └── profiler/               # Profile management for scraping
        ├── scrapper.py
        └── profile/            # Browser profiles & credentials
```

## ⚙️ Workflow

### Step 1: Document Indexing (One-time Setup)

* **Data ingestion**: Load PDFs, CSV records, and web-scraped content
* **Chunking**: Split documents into contextual chunks (400 tokens, 80 overlap)
* **Embedding**: Convert chunks to vectors using Sentence Transformers
* **FAISS Indexing**: Build vector index for semantic search
* **Output**: Store embeddings, metadata, and hashes in `index_store/`

### Step 2: Web Scraping (Parallel Collection)

* LinkedIn scraper extracts contacts and emails
* Unstop crawler collects hackathon participant data
* Google Dorking aggregates search results
* Data stored in SQLite and exported to JSON/CSV

### Step 3: User Query

The user submits a news headline, article, or claim to verify.

### Step 4: Dual Retrieval System

Two retrieval mechanisms run in parallel:

* **BM25 Retrieval**: Keyword-based matching on document chunks
* **FAISS Semantic Search**: Vector similarity search on embeddings

Results from both methods are retrieved independently.

### Step 5: Result Ranking & Fusion

* Combine results from BM25 and FAISS
* Score based on relevance and similarity metrics
* Select top-K documents

### Step 6: Verification Record Cross-Reference

* Check CSV verification datasets (Fake.csv, True.csv)
* Extract supporting or contradicting evidence
* Calculate verification confidence scores

### Step 7: Query Cache Check

* Look for cached responses to identical queries
* Return cached result if found (fast path)
* Otherwise proceed to LLM

### Step 8: Context Preparation

* Assemble top-ranked documents as context
* Include source information and evidence
* Build structured prompt

### Step 9: RAG Processing with Gemma-3

* Inject context into LLM prompt
* Generate fact-checked response
* Include source citations

### Step 10: Response Caching

* Cache the query-response pair in query_cache.json
* Update cache metadata
* Return result to user

---

## 📈 Advantages

* **High retrieval accuracy**: Hybrid BM25 + FAISS semantic search
* **Reduced hallucinations**: Evidence-grounded responses with source citations
* **Real-time data**: Multi-source web scraping for current information
* **Efficient caching**: Query caching reduces redundant LLM calls
* **Scalable architecture**: FAISS handles large document collections
* **Fast semantic search**: Vector similarity on pre-indexed embeddings
* **Lower inference costs**: Through response caching and query reuse
* **Explainable AI**: Sources and confidence scores included in responses
* **Multi-modal verification**: Combines FAISS, BM25, and CSV records
* **Production-ready**: Quantized Gemma-3 with 4-bit precision for efficiency

---

## 🎯 Use Cases

* **News Fact-Checking**: Verify news claims against indexed knowledge base
* **Misinformation Detection**: Identify potentially false claims
* **Contact Discovery**: Extract contacts from LinkedIn and Unstop
* **Event Intelligence**: Track hackathons and tech events via Unstop crawler
* **Search Intelligence**: Aggregate and analyze Google Dorking results
* **Claim Verification**: Cross-reference against CSV datasets
* **Research Assistance**: Semantic search over document collections
* **Information Retrieval**: Find relevant evidence for any query
* **Credential Verification**: Match claims against verification records

---

## 🚀 Quick Start

### Installation

1. **Clone the repository**
   ```bash
   cd /home/lucifer/Projects/RAG
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Building the Index (First-time Setup)

```bash
# Process PDFs and create FAISS index
python embeddings_builder.py --pdf your_document.pdf --run-id v1

# Or with config file
python embeddings_builder.py --config config.yaml
```

Environment variables:
```bash
export EMBED_MODEL="all-MiniLM-L6-v2"   # Embedding model
export CHUNK_SIZE="400"                  # Words per chunk
export CHUNK_OVERLAP="80"                # Word overlap
export OUTPUT_DIR="./index_store"        # Index directory
```

### Running the RAG Pipeline

```bash
# Start the pipeline with a query
python rag_pipeline.py --query "Is this news claim true?"

# With custom parameters
python rag_pipeline.py --query "Verify this claim" --top-k 5 --use-cache
```

### Web Scraping

For LinkedIn data extraction:
```bash
cd scrapping-main/linkedin
python extract_linkedin_emails.py
```

For Unstop/Devfolio data:
```bash
cd scrapping-main/unstop_crawler
python capture_devfolio_api.py
```

---

## 🔮 Future Improvements

* Multi-language support
* Source credibility scoring with ML models
* Knowledge graph integration for entity relationships
* Multi-modal analysis (images, videos)
* Advanced reranking models (ColBERT, MonoBERT)
* Real-time streaming pipelines
* Federated learning for privacy-preserving updates

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome.

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to your branch
5. Open a Pull Request

---

## 📜 License

This project is licensed under the MIT License.

---

## 👨‍💻 About F.R.I.D.A.Y.

**F.R.I.D.A.Y.** (Fact-based Retrieval Intelligence with Distributed AI & Verification Year-round) is an open-source project dedicated to building intelligent systems that combine:

* Real-time information retrieval from multiple sources
* Semantic understanding through embeddings and vector search
* LLM-powered reasoning for nuanced analysis
* Evidence-based verification against structured datasets
* Multi-modal data collection (web scraping, API integration)

**Goal**: Combat misinformation and improve trust in digital news ecosystems through accessible, explainable AI.

---

### 📧 Contact & Support

For issues, feature requests, or questions about F.R.I.D.A.Y., please open an issue on GitHub or contact the maintainers.
