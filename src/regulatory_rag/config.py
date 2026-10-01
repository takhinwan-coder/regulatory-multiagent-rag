"""Project configuration loaded from environment variables and an optional .env file."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def _project_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    chat_model: str
    embedding_model: str
    collection_name: str
    chroma_directory: Path
    pdf_directory: Path
    chunk_size: int
    chunk_overlap: int
    retrieval_k: int


def get_settings() -> Settings:
    chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "150"))
    retrieval_k = int(os.getenv("RETRIEVAL_K", "4"))
    if chunk_size <= 0:
        raise ValueError("CHUNK_SIZE must be greater than zero.")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("CHUNK_OVERLAP must be non-negative and smaller than CHUNK_SIZE.")
    if retrieval_k <= 0:
        raise ValueError("RETRIEVAL_K must be greater than zero.")

    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        chat_model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        collection_name=os.getenv("CHROMA_COLLECTION", "regulatory_documents"),
        chroma_directory=_project_path(os.getenv("CHROMA_DIRECTORY", "data/chroma_db")),
        pdf_directory=_project_path(os.getenv("PDF_DIRECTORY", "data/pdfs")),
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        retrieval_k=retrieval_k,
    )
