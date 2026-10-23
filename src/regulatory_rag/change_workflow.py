"""Deterministic source comparison and human-approved change scope."""

import difflib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader


@dataclass(frozen=True)
class ChangedPage:
    """A page-level textual change between two selected source versions."""

    old_page: int | None
    new_page: int | None
    diff: str


@dataclass(frozen=True)
class ChangeReport:
    """A reproducible comparison of two PDF source versions."""

    old_source: str
    new_source: str
    compared_at: str
    changed_pages: list[ChangedPage]


@dataclass(frozen=True)
class ScopeDecision:
    """A reviewer-approved list of internal documents for later analysis."""

    report_path: str
    selected_documents: list[str]
    decided_at: str


def compare_pdf_versions(old_path: Path, new_path: Path) -> ChangeReport:
    """Compare extracted page text without using a model."""
    for path in (old_path, new_path):
        if not path.is_file() or path.suffix.lower() != ".pdf":
            raise FileNotFoundError(f"PDF file not found: {path}")

    old_pages = [document.page_content for document in PyPDFLoader(str(old_path)).load()]
    new_pages = [document.page_content for document in PyPDFLoader(str(new_path)).load()]
    changes: list[ChangedPage] = []
    page_count = max(len(old_pages), len(new_pages))
    for page_index in range(page_count):
        old_text = old_pages[page_index] if page_index < len(old_pages) else ""
        new_text = new_pages[page_index] if page_index < len(new_pages) else ""
        if old_text == new_text:
            continue
        diff = "\n".join(
            difflib.unified_diff(
                old_text.splitlines(),
                new_text.splitlines(),
                fromfile=f"{old_path.name}:page-{page_index + 1}",
                tofile=f"{new_path.name}:page-{page_index + 1}",
                lineterm="",
            )
        )
        changes.append(
            ChangedPage(
                old_page=page_index + 1 if page_index < len(old_pages) else None,
                new_page=page_index + 1 if page_index < len(new_pages) else None,
                diff=diff,
            )
        )

    return ChangeReport(
        old_source=str(old_path),
        new_source=str(new_path),
        compared_at=datetime.now(UTC).isoformat(),
        changed_pages=changes,
    )


def write_change_report(report: ChangeReport, output_path: Path) -> None:
    """Write the complete, machine-readable report for review and later workflow steps."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(asdict(report), indent=2) + "\n", encoding="utf-8")


def load_change_report(path: Path) -> ChangeReport:
    """Load a report created by :func:`write_change_report`."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        changed_pages = [ChangedPage(**item) for item in data["changed_pages"]]
        return ChangeReport(
            old_source=data["old_source"],
            new_source=data["new_source"],
            compared_at=data["compared_at"],
            changed_pages=changed_pages,
        )
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise ValueError(f"Invalid change report: {path}") from error


def write_scope_decision(decision: ScopeDecision, output_path: Path) -> None:
    """Persist the reviewer's approved scope for a later drafting workflow."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(asdict(decision), indent=2) + "\n", encoding="utf-8")
