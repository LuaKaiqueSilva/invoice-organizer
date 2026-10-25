import unittest
from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from invoice_organizer.parsers.bank_slip_parser import BankSlipParser
from invoice_organizer.parsers.boleto_line import parse_boleto_line
from invoice_organizer.parsers.invoice_parser import InvoiceParser
from invoice_organizer.parsers.ocr import OcrUnavailableError
from invoice_organizer.parsers.parser_factory import (
    DocumentParseError,
    NoSelectableTextError,
    ParserFactory,
)


class DocumentParserTests(unittest.TestCase):
    @staticmethod
    def make_text_pdf(lines: tuple[str, ...]) -> bytes:
        writer = PdfWriter()
        page = writer.add_blank_page(width=200, height=200)
        font = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
        font_reference = writer._add_object(font)
        page[NameObject("/Resources")] = DictionaryObject(
            {
                NameObject("/Font"): DictionaryObject(
                    {NameObject("/F1"): font_reference}
                )
            }
        )
        text_commands = ["BT /F1 12 Tf 20 180 Td"]
        for line_index, line in enumerate(lines):
            escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            if line_index:
                text_commands.append("0 -16 Td")
            text_commands.append(f"({escaped}) Tj")
        text_commands.append("ET")
        content = DecodedStreamObject()
        content.set_data(" ".join(text_commands).encode("ascii"))
        page[NameObject("/Contents")] = writer._add_object(content)

        pdf = BytesIO()
        writer.write(pdf)
        return pdf.getvalue()

    def test_extracts_invoice_fields_and_brazilian_amount(self) -> None:
        parsed = InvoiceParser().parse(
            """DANFE - Documento Auxiliar da Nota Fiscal Eletrônica
            Razão social: Loja Exemplo Ltda.
            Número da nota fiscal: 004321
            Data de emissão: 15/09/2026
            Valor total da nota: R$ 1.234,56
            """
        )

        self.assertEqual(parsed.document_type, "invoice")
        self.assertEqual(parsed.issuer, "Loja Exemplo Ltda.")
        self.assertEqual(parsed.document_number, "004321")
        self.assertEqual(parsed.issue_date, "2026-09-15")
        self.assertEqual(parsed.amount, Decimal("1234.56"))

    def test_extracts_bank_slip_fields(self) -> None:
        parsed = BankSlipParser().parse(
            """Beneficiário: Fornecedor Exemplo S.A.
            Nosso número: 12345678
            Vencimento: 20/10/2026
            Valor do documento: R$ 59,90
            """
        )

        self.assertEqual(parsed.document_type, "bank_slip")
        self.assertEqual(parsed.issuer, "Fornecedor Exemplo S.A.")
        self.assertEqual(parsed.document_number, "12345678")
        self.assertEqual(parsed.due_date, "2026-10-20")
        self.assertEqual(parsed.amount, Decimal("59.90"))

    def test_included_unaccented_bank_slip_example_is_classified(self) -> None:
        example_pdf = (
            Path(__file__).resolve().parents[1] / "examples" / "example_bank_slip.pdf"
        ).read_bytes()
        parsed = ParserFactory.parse_pdf(example_pdf)

        self.assertEqual(parsed.document_type, "bank_slip")
        self.assertEqual(parsed.issuer, "Servicos Aurora Ltda.")
        self.assertEqual(parsed.amount, Decimal("89.50"))

    def test_detects_document_type_from_text(self) -> None:
        self.assertEqual(ParserFactory.detect_type("linha digitável e vencimento"), "bank_slip")
        self.assertEqual(ParserFactory.detect_type("DANFE - Nota Fiscal Eletrônica"), "invoice")
        self.assertEqual(ParserFactory.detect_type("recibo simples"), "other")

    def test_detects_bank_slip_without_accents(self) -> None:
        self.assertEqual(
            ParserFactory.detect_type("Nosso Numero Beneficiario Linha digitavel"),
            "bank_slip",
        )

    def test_preserves_issuer_starting_with_no_or_nordeste(self) -> None:
        parsed = BankSlipParser().parse("Beneficiario: Fornecedor Nordeste Ltda.")
        self.assertEqual(parsed.issuer, "Fornecedor Nordeste Ltda.")
        invoice = InvoiceParser().parse("Emitente Nova Era Ltda.")
        self.assertEqual(invoice.issuer, "Nova Era Ltda.")

    def test_does_not_take_next_line_as_issuer_when_label_is_empty(self) -> None:
        parsed = InvoiceParser().parse("Emitente:\nCNPJ: 12.345.678/0001-90")
        self.assertIsNone(parsed.issuer)

    def test_amount_requires_cents_to_avoid_reading_a_date_day(self) -> None:
        parsed = BankSlipParser().parse("Vencimento Valor do Documento\n30/10/2026")
        self.assertIsNone(parsed.amount)
        self.assertEqual(parsed.due_date, "2026-10-30")

    def test_interleaved_date_and_value_never_returns_day_as_amount(self) -> None:
        parsed = BankSlipParser().parse(
            "Vencimento Valor do Documento\n30/10/2026 89,50"
        )
        self.assertNotEqual(parsed.amount, Decimal(30))
        self.assertEqual(parsed.amount, Decimal("89.50"))
        self.assertEqual(parsed.due_date, "2026-10-30")

    def test_validates_line_digitavel_and_reads_amount_and_date(self) -> None:
        line = "033990282.7 0335666124.3 5780020101.4 8 20460000027371"
        details = parse_boleto_line(f"Linha digitável: {line}", today=date(2026, 10, 25))
        self.assertIsNotNone(details)
        self.assertEqual(details.amount, Decimal("273.71"))
        self.assertEqual(details.due_date, "2028-01-04")

        parsed = BankSlipParser().parse(f"Linha digitavel: {line}")
        self.assertEqual(parsed.amount, details.amount)
        self.assertEqual(parsed.due_date, details.due_date)

    def test_ignores_line_digitavel_with_invalid_check_digit(self) -> None:
        line = "033990282.8 0335666124.3 5780020101.4 8 20460000027371"
        self.assertIsNone(parse_boleto_line(f"Linha digitavel: {line}"))

    def test_factory_parses_a_pdf_with_the_selected_parser(self) -> None:
        with patch.object(
            ParserFactory,
            "extract_text",
            return_value="DANFE\nNúmero da nota fiscal: 888\nValor total: R$ 10,00",
        ):
            parsed = ParserFactory.parse_pdf(b"%PDF-placeholder", "auto")

        self.assertEqual(parsed.document_type, "invoice")
        self.assertEqual(parsed.document_number, "888")
        self.assertEqual(parsed.amount, Decimal("10.00"))

    def test_factory_uses_ocr_when_pdf_has_no_selectable_text(self) -> None:
        scanned_pdf = (Path(__file__).resolve().parents[1] / "examples" / "example_scanned_invoice.pdf").read_bytes()
        with patch(
            "invoice_organizer.parsers.parser_factory.extract_text_with_ocr",
            return_value=(
                "DANFE\nRazao social: Loja Exemplo Ltda.\n"
                "Numero da nota fiscal: 888\nValor total: R$ 10,00"
            ),
        ):
            parsed = ParserFactory.parse_pdf(scanned_pdf, "auto")

        self.assertEqual(parsed.document_type, "invoice")
        self.assertEqual(parsed.extraction_method, "ocr")

    def test_factory_exposes_missing_ocr_setup_for_scanned_pdf(self) -> None:
        with (
            patch(
                "invoice_organizer.parsers.parser_factory.extract_text_with_ocr",
                side_effect=OcrUnavailableError("Instale OCR local."),
            ),
            self.assertRaisesRegex(DocumentParseError, "Instale OCR local"),
        ):
                ParserFactory.parse_pdf(self.make_text_pdf(()), "auto")

    def test_ocr_fallback_uses_exception_type_not_error_message(self) -> None:
        with (
            patch.object(
                ParserFactory,
                "extract_text",
                side_effect=NoSelectableTextError("texto ausente"),
            ),
            patch(
                "invoice_organizer.parsers.parser_factory.extract_text_with_ocr",
                return_value="DANFE\nValor total: R$ 10,00",
            ),
        ):
            parsed = ParserFactory.parse_pdf(b"%PDF-placeholder", "auto")
        self.assertEqual(parsed.extraction_method, "ocr")

    def test_extracts_fields_from_a_real_text_pdf(self) -> None:
        pdf = self.make_text_pdf(
            (
                "DANFE",
                "Razao social: Loja Exemplo Ltda.",
                "Numero da nota fiscal: 54321",
                "Data de emissao: 15/09/2026",
                "Valor total da nota: R$ 1.234,56",
            )
        )

        parsed = ParserFactory.parse_pdf(pdf)

        self.assertEqual(parsed.document_type, "invoice")
        self.assertEqual(parsed.issuer, "Loja Exemplo Ltda.")
        self.assertEqual(parsed.document_number, "54321")
        self.assertEqual(parsed.issue_date, "2026-09-15")
        self.assertEqual(parsed.amount, Decimal("1234.56"))

    def test_rejects_a_valid_pdf_without_selectable_text(self) -> None:
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        pdf = BytesIO()
        writer.write(pdf)

        with self.assertRaisesRegex(DocumentParseError, "texto selecionável"):
            ParserFactory.extract_text(pdf.getvalue())

    def test_opens_pdf_with_owner_password_and_empty_user_password(self) -> None:
        source_reader = PdfReader(BytesIO(self.make_text_pdf(("DANFE", "Valor total: R$ 10,00"))))
        writer = PdfWriter()
        writer.append_pages_from_reader(source_reader)
        writer.encrypt(user_password="", owner_password="owner-secret")
        encrypted = BytesIO()
        writer.write(encrypted)

        extracted = ParserFactory.extract_text(encrypted.getvalue())
        self.assertIn("DANFE", extracted)

    def test_still_rejects_pdf_with_nonempty_open_password(self) -> None:
        source_reader = PdfReader(BytesIO(self.make_text_pdf(("DANFE",))))
        writer = PdfWriter()
        writer.append_pages_from_reader(source_reader)
        writer.encrypt(user_password="open-secret", owner_password="owner-secret")
        encrypted = BytesIO()
        writer.write(encrypted)

        with self.assertRaisesRegex(DocumentParseError, "protegido por senha"):
            ParserFactory.extract_text(encrypted.getvalue())

    def test_opens_aes_pdf_with_empty_user_password_when_crypto_extra_exists(self) -> None:
        try:
            import cryptography  # noqa: F401
        except ImportError:
            self.skipTest("AES PDF support is supplied by pypdf[crypto].")

        source_reader = PdfReader(BytesIO(self.make_text_pdf(("DANFE",))))
        writer = PdfWriter()
        writer.append_pages_from_reader(source_reader)
        writer.encrypt(user_password="", owner_password="owner-secret", algorithm="AES-256")
        encrypted = BytesIO()
        writer.write(encrypted)

        self.assertIn("DANFE", ParserFactory.extract_text(encrypted.getvalue()))


if __name__ == "__main__":
    unittest.main()
