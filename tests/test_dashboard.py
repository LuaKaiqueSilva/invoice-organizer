import unittest
from decimal import Decimal

from invoice_organizer.dashboard.app import csv_safe_cell, format_amount


class DashboardFormattingTests(unittest.TestCase):
    def test_formats_brazilian_currency(self) -> None:
        self.assertEqual(format_amount(Decimal("1234.56")), "R$ 1.234,56")

    def test_csv_escapes_spreadsheet_formula_prefixes(self) -> None:
        self.assertEqual(csv_safe_cell("=HYPERLINK(\"https://example.com\")"), "'=HYPERLINK(\"https://example.com\")")
        self.assertEqual(csv_safe_cell("Fornecedor Exemplo"), "Fornecedor Exemplo")


if __name__ == "__main__":
    unittest.main()
