# Tenant Rights RAG 🏛️⚖️

An AI-assisted legal information and guidance tool designed for tenants navigating landlord disputes in Indian metro cities (e.g., Bengaluru, Delhi NCR, Mumbai, Hyderabad, Chennai). Grounded in state-specific rent control acts, tenancy laws, model tenancy guidelines, and real case precedents via Retrieval-Augmented Generation (RAG).

> **Disclaimer:** This project is an educational, student/portfolio MVP intended for legal information and guidance, not formal legal representation or legal advice.

---

## 📁 Repository Structure

```
tenant-rag/
├── configs/               # Configuration files (model paths, RAG parameters, chunking configs)
├── data/
│   ├── raw/               # Raw statutory acts, government notifications, court judgments
│   ├── processed/         # Cleaned and standardized text documents
│   ├── chunks/            # Chunked and metadata-tagged documents ready for indexing
│   ├── embeddings/        # Vector stores and Faiss index artifacts
│   └── eval/              # Benchmark query sets, golden QA pairs, retrieval eval metrics
├── frontend/              # Minimal interactive web interface
├── notebooks/             # Exploratory analysis, data scraping, and prototyping notebooks
├── src/                   # Core application modules (scraping, chunking, retriever, API)
├── tests/                 # Unit and integration test suites
├── requirements.txt       # Local CPU and lightweight inference dependencies
└── README.md              # Project overview and setup instructions
```

---

## 🚀 Getting Started

### 1. Environment Setup

Create and activate a virtual environment:

```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note:** Heavy training and fine-tuning dependencies (`torch`, `transformers`, `peft`, `bitsandbytes`) are configured for Google Colab GPU runtimes.

---

## 🧪 Testing

Run test suites using `pytest`:

```bash
pytest
```
