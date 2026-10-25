import re
from decimal import Decimal

from invoice_organizer.models.document import ParsedDocument
from invoice_organizer.parsers.base_parser import BaseParser
from invoice_organizer.parsers.boleto_line import parse_boleto_line
from invoice_organizer.utils.text_normalization import normalize_text


class BankSlipParser(BaseParser):
    document_type = "bank_slip"
    issuer_labels = ("beneficiario", "cedente", "fornecedor")
    number_labels = (
        "nosso numero",
        "numero do documento",
    )
    amount_labels = (
        "valor do documento",
        "valor cobrado",
        "valor a pagar",
        "valor do boleto",
        "valor",
    )

    def parse(self, text: str) -> ParsedDocument:
        parsed = super().parse(text)
        boleto_details = parse_boleto_line(text)
        column_due_date, column_amount = self._extract_header_row_values(text)
        return parsed.__class__(
            document_type=parsed.document_type,
            issuer=parsed.issuer,
            document_number=parsed.document_number,
            issue_date=parsed.issue_date,
            due_date=(
                parsed.due_date
                or (boleto_details.due_date if boleto_details else None)
                or column_due_date
            ),
            amount=(
                parsed.amount
                if parsed.amount is not None
                else (boleto_details.amount if boleto_details else None) or column_amount
            ),
            extraction_method=parsed.extraction_method,
        )

    @classmethod
    def _extract_header_row_values(cls, text: str) -> tuple[str | None, Decimal | None]:
        lines = text.splitlines()
        for index, header in enumerate(lines[:-1]):
            normalized_header = normalize_text(header)
            if "vencimento" not in normalized_header or not any(
                label in normalized_header
                for label in ("valor do documento", "valor cobrado", "valor a pagar")
            ):
                continue
            value_line = next((line for line in lines[index + 1 :] if line.strip()), "")
            date_match = re.search(r"\b\d{2}[/.-]\d{2}[/.-]\d{4}\b", value_line)
            due_date = (
                cls._extract_date(f"Vencimento: {date_match.group()}", ("vencimento",))
                if date_match
                else None
            )
            amount_match = re.search(
                r"(?<![\d/-])(?:\d+(?:\.\d{3})*,\d{2}|\d+\.\d{2})(?![\d/])",
                value_line,
            )
            amount = (
                cls._parse_brazilian_amount(amount_match.group())
                if amount_match
                else None
            )
            return due_date, amount
        return None, None
