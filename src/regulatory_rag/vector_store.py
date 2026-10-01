"""Factories for the OpenAI embedding model and persistent ChromaDB store."""

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from regulatory_rag.config import Settings


def create_embeddings(settings: Settings) -> OpenAIEmbeddings:
    if not settings.openai_api_key:
        raise RuntimeError("Set OPENAI_API_KEY in your .env file before using the RAG system.")
    return OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key,
    )


def create_vector_store(settings: Settings) -> Chroma:
    settings.chroma_directory.mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name=settings.collection_name,
        embedding_function=create_embeddings(settings),
        persist_directory=str(settings.chroma_directory),
    )
