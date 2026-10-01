"""Load PDF files, split them into chunks, and index them in ChromaDB."""

import hashlib
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from regulatory_rag.config import Settings
from regulatory_rag.vector_store import create_vector_store


def ingest_pdfs(settings: Settings) -> int:
    if not settings.pdf_directory.is_dir():
        raise FileNotFoundError(
            f"PDF folder not found: {settings.pdf_directory}. Create it and add PDF files."
        )

    pdf_paths = sorted(
        path for path in settings.pdf_directory.rglob("*")
        if path.is_file() and path.suffix.lower() == ".pdf"
    )
    if not pdf_paths:
        raise FileNotFoundError(f"No PDF files found in {settings.pdf_directory}.")

    documents = []
    for pdf_path in pdf_paths:
        loaded = PyPDFLoader(str(pdf_path)).load()
        for document in loaded:
            try:
                document.metadata["source"] = str(pdf_path.relative_to(settings.pdf_directory))
            except ValueError:
                document.metadata["source"] = str(pdf_path)
            documents.append(document)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    chunks = splitter.split_documents(documents)
    if not chunks:
        raise ValueError("The PDF files did not contain any extractable text.")

    ids = []
    for chunk in chunks:
        identity = "\0".join(
            (
                chunk.metadata.get("source", ""),
                str(chunk.metadata.get("page", "")),
                chunk.page_content,
            )
        )
        ids.append(hashlib.sha256(identity.encode("utf-8")).hexdigest())

    vector_store = create_vector_store(settings)
    existing_ids = vector_store.get()["ids"]
    if existing_ids:
        vector_store.delete(ids=existing_ids)
    vector_store.add_documents(chunks, ids=ids)
    return len(chunks)
