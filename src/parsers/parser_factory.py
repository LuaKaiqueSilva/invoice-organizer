from io import BytesIO

from pypdf import PdfReader

from src.models.document import ParsedDocument
from src.parsers.bank_slip_parser import BankSlipParser
from src.parsers.base_parser import BaseParser
from src.parsers.invoice_parser import InvoiceParser


class DocumentParseError(ValueError):
    """The PDF could not be read or did not contain selectable text."""


class ParserFactory:
    @staticmethod
    def extract_text(pdf_bytes: bytes) -> str:
        try:
            reader = PdfReader(BytesIO(pdf_bytes), strict=False)
            if reader.is_encrypted:
                raise DocumentParseError("PDFs protegidos por senha não são aceitos.")
            if len(reader.pages) > 100:
                raise DocumentParseError("O PDF excede o limite de 100 páginas.")
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except DocumentParseError:
            raise
        except Exception as error:
            raise DocumentParseError("Não foi possível ler este arquivo como PDF.") from error

        if not text.strip():
            raise DocumentParseError(
                "Não encontrei texto selecionável. PDFs digitalizados ainda não têm suporte a OCR."
            )
        return text

    @staticmethod
    def detect_type(text: str) -> str:
        normalized = text.casefold()
        bank_slip_terms = (
            "linha digitável",
            "linha digitavel",
            "código de barras",
            "codigo de barras",
            "nosso número",
            "beneficiário",
        )
        invoice_terms = (
            "nota fiscal",
            "danfe",
            "chave de acesso",
            "valor total dos produtos",
        )
        if any(term in normalized for term in bank_slip_terms):
            return "bank_slip"
        if any(term in normalized for term in invoice_terms):
            return "invoice"
        return "other"

    @classmethod
    def parse_pdf(cls, pdf_bytes: bytes, selected_type: str = "auto") -> ParsedDocument:
        text = cls.extract_text(pdf_bytes)
        document_type = cls.detect_type(text) if selected_type == "auto" else selected_type
        parser: BaseParser
        if document_type == "invoice":
            parser = InvoiceParser()
        elif document_type == "bank_slip":
            parser = BankSlipParser()
        else:
            parser = BaseParser()
        return parser.parse(text)
