from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class ParsedDocument:
    document_type: str
    issuer: str | None = None
    document_number: str | None = None
    issue_date: str | None = None
    due_date: str | None = None
    amount: Decimal | None = None


@dataclass(frozen=True)
class Document:
    id: str
    file_name: str
    stored_name: str
    document_type: str
    issuer: str | None
    document_number: str | None
    issue_date: str | None
    due_date: str | None
    amount: Decimal | None
    sha256: str
    created_at: datetime
