# Multi-Agent RAG System for Regulatory Policy Change Management

This repository currently contains a minimal, single-agent PDF RAG foundation for the capstone. It loads local PDFs, indexes their chunks in ChromaDB using OpenAI embeddings, and answers questions with source/page citations. The [project blueprint](PROJECT_BLUEPRINT.md) outlines the proposed scope, architecture, and phased path toward regulatory change analysis with multiple agents; LLMOps evaluation is deferred.

## Project layout

```text
regulatory-multiagent-rag/
├── data/
│   └── pdfs/                 # Put source PDFs here (subfolders are supported)
├── src/
│   └── regulatory_rag/
│       ├── __init__.py
│       ├── cli.py             # Ingest and interactive/query command-line interface
│       ├── config.py          # Environment and project settings
│       ├── ingestion.py       # PDF loading, chunking, and Chroma indexing
│       ├── query.py           # Retrieval, answer generation, and citations
│       └── vector_store.py    # OpenAI embeddings and ChromaDB construction
├── .env.example               # Copy to .env and add your OpenAI API key
├── .gitignore
└── pyproject.toml             # Package metadata and dependencies
```

## Setup in VS Code on Windows

Open this folder in VS Code, then run the following commands in a PowerShell terminal:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
Copy-Item .env.example .env
```

Open `.env` and set `OPENAI_API_KEY` to your API key. Do not commit `.env`. Place the PDFs you want to search in `data/pdfs/`; nested folders are searched too.

## Use

Build or refresh the local ChromaDB index:

```powershell
python -m regulatory_rag.cli ingest
```

Ask one question:

```powershell
python -m regulatory_rag.cli ask "What are the main reporting obligations?"
```

Run `ask` without a question to enter interactive mode; type `exit` or `quit` to stop. Answers include numbered citations, followed by each cited PDF path and page number. Re-running `ingest` refreshes the collection from the PDFs currently in `data/pdfs/`.

The `.env` file supports optional `OPENAI_CHAT_MODEL`, `OPENAI_EMBEDDING_MODEL`, `CHROMA_COLLECTION`, `CHROMA_DIRECTORY`, `PDF_DIRECTORY`, `CHUNK_SIZE`, `CHUNK_OVERLAP`, and `RETRIEVAL_K` settings. Paths may be absolute or relative to the project root.
