"""Command-line interface for ingestion, retrieval, and change review."""

import argparse
from datetime import UTC, datetime
from pathlib import Path

from regulatory_rag.change_workflow import (
    ScopeDecision,
    compare_pdf_versions,
    load_change_report,
    write_change_report,
    write_scope_decision,
)
from regulatory_rag.config import get_settings
from regulatory_rag.ingestion import ingest_pdfs
from regulatory_rag.query import answer_question, format_answer


def _default_report_path(old_pdf: Path, new_pdf: Path) -> Path:
    return Path("data/change_reports") / f"{old_pdf.stem}--{new_pdf.stem}.json"


def _default_scope_path(report_path: Path) -> Path:
    return Path("data/scope_decisions") / f"{report_path.stem}-scope.json"


def _review_scope(report_path: Path, candidates: list[str]) -> ScopeDecision:
    report = load_change_report(report_path)
    print(
        f"Reviewed change report: {report_path}\n"
        f"Source versions: {report.old_source} -> {report.new_source}\n"
        f"Changed pages: {len(report.changed_pages)}\n"
    )
    selected_documents = []
    for candidate in candidates:
        answer = input(f"Include '{candidate}' in the drafting scope? [y/N] ").strip().lower()
        if answer in {"y", "yes"}:
            selected_documents.append(candidate)

    while True:
        additional = input("Add another document to the scope (or press Enter to finish): ").strip()
        if not additional:
            break
        selected_documents.append(additional)

    return ScopeDecision(
        report_path=str(report_path),
        selected_documents=selected_documents,
        decided_at=datetime.now(UTC).isoformat(),
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Index regulatory PDFs, ask cited questions, and review version changes."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("ingest", help="Load PDFs and refresh the ChromaDB index.")
    ask_parser = commands.add_parser("ask", help="Ask a question or start interactive mode.")
    ask_parser.add_argument("question", nargs="?", help="Question to ask.")
    compare_parser = commands.add_parser(
        "compare", help="Create a deterministic page-level comparison of two PDF versions."
    )
    compare_parser.add_argument("old_pdf", type=Path, help="Earlier authoritative PDF version.")
    compare_parser.add_argument("new_pdf", type=Path, help="Later authoritative PDF version.")
    compare_parser.add_argument(
        "--output",
        type=Path,
        help="Path for the JSON change report (default: data/change_reports/<old>--<new>.json).",
    )
    scope_parser = commands.add_parser(
        "review-scope",
        help="Interactively approve candidate documents before a later drafting step.",
    )
    scope_parser.add_argument(
        "report", type=Path, help="Change report produced by the compare command."
    )
    scope_parser.add_argument(
        "--candidate",
        action="append",
        default=[],
        help="Candidate internal document path or identifier. Repeat for each candidate.",
    )
    scope_parser.add_argument(
        "--output",
        type=Path,
        help="Path for the approved-scope JSON (default: data/scope_decisions/<report>-scope.json).",
    )
    args = parser.parse_args()
    settings = get_settings()

    try:
        if args.command == "ingest":
            count = ingest_pdfs(settings)
            print(f"Indexed {count} text chunks.")
            return

        if args.command == "compare":
            output_path = args.output or _default_report_path(args.old_pdf, args.new_pdf)
            report = compare_pdf_versions(args.old_pdf, args.new_pdf)
            write_change_report(report, output_path)
            print(f"Saved {len(report.changed_pages)} changed page(s) to {output_path}.")
            return

        if args.command == "review-scope":
            output_path = args.output or _default_scope_path(args.report)
            decision = _review_scope(args.report, args.candidate)
            write_scope_decision(decision, output_path)
            print(
                f"Saved an approved scope with {len(decision.selected_documents)} document(s) "
                f"to {output_path}."
            )
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
