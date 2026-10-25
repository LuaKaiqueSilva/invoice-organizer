import sqlite3
import tempfile
import unittest
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from src.models.document import Document
from src.repositories.document_repository import DocumentRepository


class DocumentRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test.sqlite3"
        self.repository = DocumentRepository(self.database_path)
        self.document = Document(
            id="doc-1",
            file_name="nota.pdf",
            stored_name="random.pdf",
            document_type="invoice",
            issuer="Loja Exemplo",
            document_number="123",
            issue_date="2026-09-15",
            due_date=None,
            amount=Decimal("12.34"),
            sha256="digest-1",
            created_at=datetime(2026, 9, 15, 12, 30),
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_adds_and_reads_document_fields(self) -> None:
        self.repository.add(self.document)

        found = self.repository.get_by_id("doc-1")
        self.assertEqual(found, self.document)
        self.assertEqual(self.repository.get_by_hash("digest-1"), self.document)
        self.assertEqual(self.repository.list_all(), [self.document])

    def test_hash_is_unique(self) -> None:
        self.repository.add(self.document)
        duplicate_hash = Document(
            **{**self.document.__dict__, "id": "doc-2", "stored_name": "other.pdf"}
        )

        with self.assertRaises(sqlite3.IntegrityError):
            self.repository.add(duplicate_hash)

    def test_migrates_database_created_before_extraction_method_column(self) -> None:
        legacy_path = Path(self.temp_dir.name) / "legacy.sqlite3"
        with sqlite3.connect(legacy_path) as connection:
            connection.execute(
                """CREATE TABLE documents (
                    id TEXT PRIMARY KEY, file_name TEXT NOT NULL, stored_name TEXT NOT NULL UNIQUE,
                    document_type TEXT NOT NULL, issuer TEXT, document_number TEXT,
                    issue_date TEXT, due_date TEXT, amount TEXT, sha256 TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL
                )"""
            )

        self.assertEqual(DocumentRepository(legacy_path).list_all(), [])
        with sqlite3.connect(legacy_path) as connection:
            columns = {row[1] for row in connection.execute("PRAGMA table_info(documents)")}
        self.assertIn("extraction_method", columns)


if __name__ == "__main__":
    unittest.main()
