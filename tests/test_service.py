import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from invoice_organizer.models.document import ParsedDocument
from invoice_organizer.repositories.document_repository import DocumentRepository
from invoice_organizer.services.document_service import DocumentService
from invoice_organizer.services.exceptions import DocumentImportError, DuplicateDocumentError


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

    def test_updates_document_metadata_with_brazilian_amount(self) -> None:
        document = self.service.import_pdf("invoice.pdf", self.pdf_bytes)

        updated = self.service.update_metadata(
            document.id, "Loja Corrigida", "NF 99", "2026-10-21", "", "R$ 1.234,56"
        )

        self.assertEqual(updated.issuer, "Loja Corrigida")
        self.assertEqual(updated.document_number, "NF 99")
        self.assertEqual(updated.issue_date, "2026-10-21")
        self.assertIsNone(updated.due_date)
        self.assertEqual(updated.amount, Decimal("1234.56"))

    def test_parses_dot_grouped_amount_as_thousands(self) -> None:
        document = self.service.import_pdf("invoice.pdf", self.pdf_bytes)

        updated = self.service.update_metadata(
            document.id, "", "", "", "", "1.500"
        )

        self.assertEqual(updated.amount, Decimal(1500))

    def test_rejects_negative_manual_amount(self) -> None:
        document = self.service.import_pdf("invoice.pdf", self.pdf_bytes)

        with self.assertRaisesRegex(DocumentImportError, "não negativo"):
            self.service.update_metadata(document.id, "", "", "", "", "-1,00")

    def test_rejects_invalid_manual_date(self) -> None:
        document = self.service.import_pdf("invoice.pdf", self.pdf_bytes)

        with self.assertRaisesRegex(DocumentImportError, "AAAA-MM-DD"):
            self.service.update_metadata(document.id, "", "", "21/10/2026", "", "")

    def test_deletes_document_and_stored_pdf(self) -> None:
        document = self.service.import_pdf("invoice.pdf", self.pdf_bytes)
        stored_path = self.root / "documents" / document.stored_name
        self.assertTrue(stored_path.exists())

        self.assertTrue(self.service.delete_document(document.id))

        self.assertFalse(stored_path.exists())
        self.assertEqual(self.service.list_documents(), [])


if __name__ == "__main__":
    unittest.main()
