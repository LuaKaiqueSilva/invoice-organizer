from datetime import datetime
from decimal import Decimal
from pathlib import Path

from src.config.settings import DATABASE_PATH
from src.database.connection import get_connection
from src.models.document import Document


class DocumentRepository:
    def __init__(self, database_path: Path = DATABASE_PATH) -> None:
        self.database_path = database_path

    @staticmethod
    def _from_row(row) -> Document:
        return Document(
            id=row["id"],
            file_name=row["file_name"],
            stored_name=row["stored_name"],
            document_type=row["document_type"],
            issuer=row["issuer"],
            document_number=row["document_number"],
            issue_date=row["issue_date"],
            due_date=row["due_date"],
            amount=Decimal(row["amount"]) if row["amount"] is not None else None,
            sha256=row["sha256"],
            created_at=datetime.fromisoformat(row["created_at"]),
            extraction_method=row["extraction_method"],
        )

    def add(self, document: Document) -> None:
        with get_connection(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO documents (
                    id, file_name, stored_name, document_type, issuer,
                    document_number, issue_date, due_date, amount, sha256, created_at,
                    extraction_method
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document.id,
                    document.file_name,
                    document.stored_name,
                    document.document_type,
                    document.issuer,
                    document.document_number,
                    document.issue_date,
                    document.due_date,
                    str(document.amount) if document.amount is not None else None,
                    document.sha256,
                    document.created_at.isoformat(),
                    document.extraction_method,
                ),
            )

    def get_by_hash(self, sha256: str) -> Document | None:
        with get_connection(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM documents WHERE sha256 = ?", (sha256,)
            ).fetchone()
        return self._from_row(row) if row else None

    def get_by_id(self, document_id: str) -> Document | None:
        with get_connection(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM documents WHERE id = ?", (document_id,)
            ).fetchone()
        return self._from_row(row) if row else None

    def list_all(self) -> list[Document]:
        with get_connection(self.database_path) as connection:
            rows = connection.execute(
                "SELECT * FROM documents ORDER BY created_at DESC, file_name COLLATE NOCASE"
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def update_metadata(
        self,
        document_id: str,
        issuer: str | None,
        document_number: str | None,
        issue_date: str | None,
        due_date: str | None,
        amount: Decimal | None,
    ) -> Document | None:
        with get_connection(self.database_path) as connection:
            cursor = connection.execute(
                """UPDATE documents SET issuer = ?, document_number = ?, issue_date = ?,
                   due_date = ?, amount = ? WHERE id = ?""",
                (
                    issuer,
                    document_number,
                    issue_date,
                    due_date,
                    str(amount) if amount is not None else None,
                    document_id,
                ),
            )
            if cursor.rowcount == 0:
                return None
            row = connection.execute(
                "SELECT * FROM documents WHERE id = ?", (document_id,)
            ).fetchone()
        return self._from_row(row) if row else None

    def delete(self, document_id: str) -> Document | None:
        with get_connection(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM documents WHERE id = ?", (document_id,)
            ).fetchone()
            if row is None:
                return None
            connection.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        return self._from_row(row)
