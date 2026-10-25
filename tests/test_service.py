import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from src.models.document import ParsedDocument
from src.repositories.document_repository import DocumentRepository
from src.services.document_service import DocumentService
from src.services.exceptions import DocumentImportError, DuplicateDocumentError


class StubParserFactory:
    @staticmethod
    def parse_pdf(_content: bytes, selected_type: str) -> ParsedDocument:
        return ParsedDocument(
            document_type="invoice" if selected_type == "auto" else selected_type,
            issuer="Loja Exemplo",
            document_number="NF 42",
            issue_date="2026-09-15",
            amount=Decimal("123.45"),
        )


class DocumentServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.service = DocumentService(
            repository=DocumentRepository(self.root / "db.sqlite3"),
            documents_dir=self.root / "documents",
            max_size_bytes=100,
            parser_factory=StubParserFactory,
        )
        self.pdf_bytes = b"%PDF-1.4\nsynthetic pdf content"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_imports_pdf_and_keeps_original_for_download(self) -> None:
        document = self.service.import_pdf("invoice.pdf", self.pdf_bytes)

        self.assertEqual(document.document_type, "invoice")
        self.assertEqual(document.amount, Decimal("123.45"))
        self.assertEqual(self.service.list_documents(), [document])
        self.assertEqual(self.service.get_pdf_bytes(document.id), ("invoice.pdf", self.pdf_bytes))

    def test_rejects_duplicate_pdf(self) -> None:
        self.service.import_pdf("invoice.pdf", self.pdf_bytes)

        with self.assertRaises(DuplicateDocumentError):
            self.service.import_pdf("renamed.pdf", self.pdf_bytes)

    def test_rejects_bad_extension_and_invalid_pdf_signature(self) -> None:
        with self.assertRaisesRegex(DocumentImportError, "extensão .pdf"):
            self.service.import_pdf("invoice.txt", self.pdf_bytes)
        with self.assertRaisesRegex(DocumentImportError, "PDF válido"):
            self.service.import_pdf("invoice.pdf", b"not a pdf")

    def test_rejects_files_over_size_limit(self) -> None:
        with self.assertRaisesRegex(DocumentImportError, "limite"):
            self.service.import_pdf("large.pdf", self.pdf_bytes + b"x" * 100)


if __name__ == "__main__":
    unittest.main()
