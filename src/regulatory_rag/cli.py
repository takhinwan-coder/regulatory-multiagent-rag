"""Command-line interface for PDF ingestion and question answering."""

import argparse

from regulatory_rag.config import get_settings
from regulatory_rag.ingestion import ingest_pdfs
from regulatory_rag.query import answer_question, format_answer


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Index regulatory PDFs and ask questions with source citations."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("ingest", help="Load PDFs and refresh the ChromaDB index.")
    ask_parser = commands.add_parser("ask", help="Ask a question or start interactive mode.")
    ask_parser.add_argument("question", nargs="?", help="Question to ask.")
    args = parser.parse_args()
    settings = get_settings()

    try:
        if args.command == "ingest":
            count = ingest_pdfs(settings)
            print(f"Indexed {count} text chunks.")
            return

        if args.question:
            print(format_answer(answer_question(args.question, settings)))
            return

        while True:
            question = input("\nQuestion (or 'exit' to quit): ").strip()
            if question.lower() in {"exit", "quit"}:
                break
            if not question:
                continue
            print(format_answer(answer_question(question, settings)))
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
