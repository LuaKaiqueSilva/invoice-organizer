import re
from abc import ABC
from datetime import datetime
from decimal import Decimal, InvalidOperation

from src.models.document import ParsedDocument


class BaseParser(ABC):
    document_type = "other"
    issuer_labels = ("emitente", "fornecedor", "beneficiário", "beneficiario", "cedente")
    number_labels = ("número da nota", "numero da nota", "número do documento", "nosso número", "nosso numero")
    amount_labels = (
        "valor total da nota",
        "valor total da fatura",
        "total a pagar",
        "valor do documento",
        "valor cobrado",
        "valor a pagar",
        "valor total",
        "valor",
    )

    def parse(self, text: str) -> ParsedDocument:
        normalized = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        return ParsedDocument(
            document_type=self.document_type,
            issuer=self._extract_labeled_text(normalized, self.issuer_labels),
            document_number=self._extract_labeled_text(normalized, self.number_labels),
            issue_date=self._extract_date(normalized, ("data de emissão", "data de emissao", "emissão", "emissao")),
            due_date=self._extract_date(normalized, ("data de vencimento", "vencimento")),
            amount=self._extract_amount(normalized),
        )

    @staticmethod
    def _extract_labeled_text(text: str, labels: tuple[str, ...]) -> str | None:
        label_pattern = "|".join(re.escape(label) for label in labels)
        match = re.search(
            rf"(?:{label_pattern})\s*(?:n[º°o]\s*)?[:\-]?\s*([^\n|;]+)",
            text,
            flags=re.IGNORECASE,
        )
        if not match:
            return None
        value = match.group(1).strip(" \t:-")
        return value[:160] or None

    @staticmethod
    def _extract_date(text: str, labels: tuple[str, ...]) -> str | None:
        label_pattern = "|".join(re.escape(label) for label in labels)
        match = re.search(
            rf"(?:{label_pattern})\s*[:\-]?\s*(\d{{2}}[/.\-]\d{{2}}[/.\-]\d{{4}}|\d{{4}}-\d{{2}}-\d{{2}})",
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
        for label in self.amount_labels:
            match = re.search(
                rf"{re.escape(label)}\s*[:\-]?\s*(?:R\$\s*)?([\d.]+(?:,\d{{1,2}})?|[\d,]+(?:\.\d{{1,2}})?)",
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
            cleaned = cleaned.replace(".", "").replace(",", ".")
        elif cleaned.count(".") > 1:
            parts = cleaned.split(".")
            cleaned = "".join(parts[:-1]) + "." + parts[-1]
        return Decimal(cleaned)
