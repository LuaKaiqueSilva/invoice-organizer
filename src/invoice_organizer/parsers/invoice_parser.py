from invoice_organizer.parsers.base_parser import BaseParser


class InvoiceParser(BaseParser):
    document_type = "invoice"
    issuer_labels = ("emitente", "fornecedor", "razão social", "razao social")
    number_labels = (
        "numero da nota fiscal",
        "numero da nota",
        "nota fiscal no",
        "nfe no",
    )
    amount_labels = (
        "valor total da nota",
        "valor total dos produtos",
        "valor total da fatura",
        "valor total",
        "total da nota",
    )
