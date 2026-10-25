import re
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal


@dataclass(frozen=True)
class BoletoLineDetails:
    amount: Decimal | None
    due_date: str | None


def _mod10_digit(value: str) -> int:
    total = 0
    multiplier = 2
    for character in reversed(value):
        product = int(character) * multiplier
        total += product // 10 + product % 10
        multiplier = 1 if multiplier == 2 else 2
    return (-total) % 10


def _barcode_digit_is_valid(barcode: str) -> bool:
    body = barcode[:4] + barcode[5:]
    total = 0
    weight = 2
    for character in reversed(body):
        total += int(character) * weight
        weight = 2 if weight == 9 else weight + 1
    digit = (total * 10) % 11
    expected = 1 if digit in {0, 1, 10} else digit
    return int(barcode[4]) == expected


def _valid_line(line: str) -> bool:
    if len(line) != 47 or not line.isdigit() or line[3] != "9":
        return False
    fields = ((line[0:9], line[9]), (line[10:20], line[20]), (line[21:31], line[31]))
    if any(_mod10_digit(field) != int(check) for field, check in fields):
        return False

    barcode = (
        line[0:4]
        + line[32]
        + line[33:47]
        + line[4:9]
        + line[10:20]
        + line[21:31]
    )
    return _barcode_digit_is_valid(barcode)


def _due_date_from_factor(factor_text: str, today: date) -> str | None:
    factor = int(factor_text)
    if factor == 0:
        return None

    old_base = date(1997, 10, 7)
    candidates = [old_base + timedelta(days=factor)]
    if factor >= 1000:
        # FEBRABAN restarted the factor at 1000 on 22 February 2025.
        new_base = date(2025, 2, 22)
        candidates.append(new_base + timedelta(days=factor - 1000))
    return min(candidates, key=lambda candidate: abs((candidate - today).days)).isoformat()


def parse_boleto_line(text: str, today: date | None = None) -> BoletoLineDetails | None:
    """Read amount and due-date hints only from a checksum-valid 47-digit line."""
    reference_date = today or date.today()
    for raw_line in text.splitlines():
        digits = "".join(re.findall(r"\d", raw_line))
        if len(digits) < 47:
            continue
        for start in range(len(digits) - 46):
            candidate = digits[start : start + 47]
            if not _valid_line(candidate):
                continue
            factor = candidate[33:37]
            amount_cents = int(candidate[37:47])
            return BoletoLineDetails(
                amount=Decimal(amount_cents) / Decimal(100) if amount_cents else None,
                due_date=_due_date_from_factor(factor, reference_date),
            )
    return None
