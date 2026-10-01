"""Retrieve relevant PDF chunks and generate answers with source citations."""

from dataclasses import dataclass
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from regulatory_rag.config import PROJECT_ROOT, Settings
from regulatory_rag.vector_store import create_vector_store


@dataclass(frozen=True)
class Citation:
    number: int
    source: str
    page: int | None


@dataclass(frozen=True)
class RAGAnswer:
    answer: str
    citations: list[Citation]


def _citation_location(metadata: dict, number: int) -> Citation:
    source = str(metadata.get("source", "Unknown source"))
    source_path = Path(source)
    if source_path.is_absolute():
        try:
            source = str(source_path.resolve().relative_to(PROJECT_ROOT))
        except ValueError:
            source = source_path.name

    page = metadata.get("page")
    try:
        displayed_page = int(page) + 1 if page is not None else None
    except (TypeError, ValueError):
        displayed_page = None
    return Citation(number=number, source=source, page=displayed_page)


def answer_question(question: str, settings: Settings) -> RAGAnswer:
    question = question.strip()
    if not question:
        raise ValueError("Enter a question.")

    vector_store = create_vector_store(settings)
    if not vector_store.get()["ids"]:
        raise RuntimeError("The ChromaDB index is empty. Run the ingest command first.")

    documents = vector_store.similarity_search(question, k=settings.retrieval_k)
    if not documents:
        raise RuntimeError("No matching document chunks were found.")

    citations = [_citation_location(document.metadata, index) for index, document in enumerate(documents, 1)]
    context = "\n\n".join(
        f"[{citation.number}] Source: {citation.source}"
        f"{f', page {citation.page}' if citation.page is not None else ''}\n"
        f"{document.page_content}"
        for citation, document in zip(citations, documents)
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Answer the question using only the provided document excerpts. "
                "Cite supporting statements with the excerpt's citation number, such as [1]. "
                "If the excerpts do not contain the answer, say that the available documents "
                "do not provide enough information. Do not invent facts or citations.",
            ),
            ("human", "Question: {question}\n\nDocument excerpts:\n{context}"),
        ]
    )
    model = ChatOpenAI(
        model=settings.chat_model,
        api_key=settings.openai_api_key,
        temperature=0,
    )
    response = model.invoke(prompt.format_messages(question=question, context=context))
    return RAGAnswer(answer=str(response.content), citations=citations)


def format_answer(result: RAGAnswer) -> str:
    lines = [result.answer, "", "Sources:"]
    for citation in result.citations:
        page = f", page {citation.page}" if citation.page is not None else ""
        lines.append(f"[{citation.number}] {citation.source}{page}")
    return "\n".join(lines)
