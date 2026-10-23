"""Load and validate version metadata for regulatory source documents."""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DocumentMetadata:
    """Provenance needed to filter and compare a regulatory document."""

    source: str
    document_id: str
    title: str
    jurisdiction: str
    regulator: str
    document_type: str
    version: str
    publication_date: str | None = None
    effective_date: str | None = None
    status: str | None = None
    superseded_by: str | None = None

    def chroma_metadata(self) -> dict[str, str]:
        values = {
            "document_id": self.document_id,
            "title": self.title,
            "jurisdiction": self.jurisdiction,
            "regulator": self.regulator,
            "document_type": self.document_type,
            "version": self.version,
            "publication_date": self.publication_date,
            "effective_date": self.effective_date,
            "status": self.status,
            "superseded_by": self.superseded_by,
        }
        return {key: value for key, value in values.items() if value is not None}


def load_document_metadata(path: Path) -> dict[str, DocumentMetadata]:
    """Return metadata keyed by the PDF path relative to the PDF directory."""
    if not path.exists():
        return {}

    try:
        contents = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Document metadata file is not valid JSON: {path}") from error

    documents = contents.get("documents")
    if not isinstance(documents, list):
        raise ValueError("Document metadata must contain a 'documents' list.")

    metadata_by_source: dict[str, DocumentMetadata] = {}
    required_fields = (
        "source",
        "document_id",
        "title",
        "jurisdiction",
        "regulator",
        "document_type",
        "version",
    )
    optional_fields = ("publication_date", "effective_date", "status", "superseded_by")
    for index, item in enumerate(documents, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Document metadata entry {index} must be an object.")
        missing = [field for field in required_fields if not str(item.get(field, "")).strip()]
        if missing:
            raise ValueError(
                f"Document metadata entry {index} is missing required field(s): {', '.join(missing)}."
            )
        unknown = set(item) - set(required_fields) - set(optional_fields)
        if unknown:
            raise ValueError(
                f"Document metadata entry {index} contains unsupported field(s): "
                f"{', '.join(sorted(unknown))}."
            )

        source = str(item["source"]).replace("\\", "/").strip()
        if Path(source).is_absolute() or source.startswith("../"):
            raise ValueError(
                f"Document metadata entry {index} must use a relative PDF source path."
            )
        if source in metadata_by_source:
            raise ValueError(f"Document metadata duplicates source path: {source}.")

        metadata_by_source[source] = DocumentMetadata(
            **{field: str(item[field]).strip() for field in required_fields},
            **{
                field: str(item[field]).strip() if item.get(field) is not None else None
                for field in optional_fields
            },
        )

    return metadata_by_source
