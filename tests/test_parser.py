import unittest
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from src.parsers.bank_slip_parser import BankSlipParser
from src.parsers.invoice_parser import InvoiceParser
from src.parsers.parser_factory import DocumentParseError, ParserFactory


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

    def test_detects_document_type_from_text(self) -> None:
        self.assertEqual(ParserFactory.detect_type("linha digitável e vencimento"), "bank_slip")
        self.assertEqual(ParserFactory.detect_type("DANFE - Nota Fiscal Eletrônica"), "invoice")
        self.assertEqual(ParserFactory.detect_type("recibo simples"), "other")

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
            "src.parsers.parser_factory.extract_text_with_ocr",
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
                "src.parsers.parser_factory.extract_text_with_ocr",
                side_effect=RuntimeError("Instale OCR local."),
            ),
            self.assertRaisesRegex(DocumentParseError, "Instale OCR local"),
        ):
                ParserFactory.parse_pdf(self.make_text_pdf(()), "auto")

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


if __name__ == "__main__":
    unittest.main()
