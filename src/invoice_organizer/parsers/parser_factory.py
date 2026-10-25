from io import BytesIO

from pypdf import PdfReader

from invoice_organizer.models.document import ParsedDocument
from invoice_organizer.parsers.bank_slip_parser import BankSlipParser
from invoice_organizer.parsers.base_parser import BaseParser
from invoice_organizer.parsers.invoice_parser import InvoiceParser
from invoice_organizer.parsers.ocr import OcrError, extract_text_with_ocr
from invoice_organizer.utils.text_normalization import normalize_text


class DocumentParseError(ValueError):
    """The PDF could not be read or did not contain selectable text."""


class NoSelectableTextError(DocumentParseError):
    """The PDF is valid but has no text layer, so OCR may be needed."""


class ParserFactory:
    @staticmethod
    def extract_text(pdf_bytes: bytes) -> str:
        try:
            reader = PdfReader(BytesIO(pdf_bytes), strict=False)
            if reader.is_encrypted:
                try:
                    decrypted = reader.decrypt("")
                except Exception as error:
                    raise DocumentParseError(
                        "Este PDF está protegido por senha e não pode ser aberto sem ela."
                    ) from error
                if not decrypted:
                    raise DocumentParseError(
                        "Este PDF está protegido por senha e não pode ser aberto sem ela."
                    )
            if len(reader.pages) > 100:
                raise DocumentParseError("O PDF excede o limite de 100 páginas.")
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except DocumentParseError:
            raise
        except Exception as error:
            raise DocumentParseError("Não foi possível ler este arquivo como PDF.") from error

        if not text.strip():
            raise NoSelectableTextError(
                "Não encontrei texto selecionável neste PDF."
            )
        return text

    @staticmethod
    def detect_type(text: str) -> str:
        normalized = normalize_text(text)
        bank_slip_terms = (
            "linha digitavel",
            "codigo de barras",
            "nosso numero",
            "beneficiario",
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
        try:
            text = cls.extract_text(pdf_bytes)
            extraction_method = "text"
        except NoSelectableTextError:
            try:
                text = extract_text_with_ocr(pdf_bytes)
            except OcrError as ocr_error:
                raise DocumentParseError(str(ocr_error)) from ocr_error
            if not text.strip():
                raise DocumentParseError(
                    "O OCR não reconheceu texto neste PDF. Tente um arquivo mais nítido."
                )
            extraction_method = "ocr"
        document_type = cls.detect_type(text) if selected_type == "auto" else selected_type
        parser: BaseParser
        if document_type == "invoice":
            parser = InvoiceParser()
        elif document_type == "bank_slip":
            parser = BankSlipParser()
        else:
            parser = BaseParser()
        parsed = parser.parse(text)
        return ParsedDocument(
            document_type=parsed.document_type,
            issuer=parsed.issuer,
            document_number=parsed.document_number,
            issue_date=parsed.issue_date,
            due_date=parsed.due_date,
            amount=parsed.amount,
            extraction_method=extraction_method,
        )
