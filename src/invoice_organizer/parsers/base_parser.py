import re
from abc import ABC
from datetime import datetime
from decimal import Decimal, InvalidOperation

from invoice_organizer.models.document import ParsedDocument
from invoice_organizer.utils.text_normalization import normalize_text, normalize_text_with_mapping


class BaseParser(ABC):
    document_type = "other"
    issuer_labels = ("emitente", "fornecedor", "beneficiario", "cedente")
    number_labels = ("numero da nota", "numero do documento", "nosso numero")
    amount_labels = (
        "valor total da nota",
        "valor total da fatura",
        "total a pagar",
        "valor do documento",
        "valor cobrado",
        "valor a pagar",
        "valor do boleto",
        "valor total",
        "valor",
    )

    def parse(self, text: str) -> ParsedDocument:
        original = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        normalized, original_indexes = normalize_text_with_mapping(original)
        return ParsedDocument(
            document_type=self.document_type,
            issuer=self._extract_labeled_text(
                original, normalized, original_indexes, self.issuer_labels
            ),
            document_number=self._extract_labeled_text(
                original, normalized, original_indexes, self.number_labels
            ),
            issue_date=self._extract_date(normalized, ("data de emissao", "emissao")),
            due_date=self._extract_date(normalized, ("data de vencimento", "vencimento")),
            amount=self._extract_amount(normalized),
        )

    @staticmethod
    def _extract_labeled_text(
        original: str,
        normalized: str,
        original_indexes: list[int],
        labels: tuple[str, ...],
    ) -> str | None:
        label_pattern = "|".join(
            re.escape(normalize_text(label)) for label in sorted(labels, key=len, reverse=True)
        )
        match = re.search(
            rf"(?:{label_pattern})[ \t]*(?:n[º°]|no(?=[ \t.:]))?[ \t]*[:\-]?[ \t]*([^\n|;]+)",
            normalized,
            flags=re.IGNORECASE,
        )
        if not match:
            return None
        start, end = match.span(1)
        original_start = original_indexes[start]
        original_end = original_indexes[end - 1] + 1
        value = original[original_start:original_end].strip(" \t:-")
        return value[:160] or None

    @staticmethod
    def _extract_date(text: str, labels: tuple[str, ...]) -> str | None:
        label_pattern = "|".join(
            re.escape(normalize_text(label)) for label in sorted(labels, key=len, reverse=True)
        )
        match = re.search(
            rf"(?:{label_pattern})[ \t]*[:\-]?[ \t]*(\d{{2}}[/.-]\d{{2}}[/.-]\d{{4}}|\d{{4}}-\d{{2}}-\d{{2}})",
            text,
            flags=re.IGNORECASE,
        )
        if not match:
            return None
        value = match.group(1)
        for date_format in ("%d/%m/%Y", "%d.%m.%Y", "%d-%m-%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, date_format).date().isoformat()
            except ValueError:
                continue
        return None

    def _extract_amount(self, text: str) -> Decimal | None:
        # Require cents so a day/month from an adjacent date cannot masquerade
        # as a plausible amount when a PDF layout interleaves columns.
        for label in self.amount_labels:
            match = re.search(
                rf"{re.escape(normalize_text(label))}\s*[:\-]?\s*(?:r\$\s*)?(\d+(?:\.\d{{3}})*,\d{{2}}|\d+\.\d{{2}})",
                text,
                flags=re.IGNORECASE,
            )
            if match:
                try:
                    return self._parse_brazilian_amount(match.group(1))
                except InvalidOperation:
                    continue
        return None

    @staticmethod
    def _parse_brazilian_amount(value: str) -> Decimal:
        cleaned = value.strip()
        if "," in cleaned and "." in cleaned:
            if cleaned.rfind(",") > cleaned.rfind("."):
                cleaned = cleaned.replace(".", "").replace(",", ".")
            else:
                cleaned = cleaned.replace(",", "")
        elif "," in cleaned:
            cleaned = cleaned.replace(",", ".")
        elif cleaned.count(".") > 1:
            parts = cleaned.split(".")
            cleaned = "".join(parts[:-1]) + "." + parts[-1]
        return Decimal(cleaned)
