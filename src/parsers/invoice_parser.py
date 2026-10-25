from src.parsers.base_parser import BaseParser


class InvoiceParser(BaseParser):
    document_type = "invoice"
    issuer_labels = ("emitente", "fornecedor", "razão social", "razao social")
    number_labels = (
        "número da nota fiscal",
        "numero da nota fiscal",
        "número da nota",
        "numero da nota",
        "nota fiscal nº",
        "nota fiscal n°",
        "nfe nº",
        "nfe n°",
    )
    amount_labels = (
        "valor total da nota",
        "valor total dos produtos",
        "valor total da fatura",
        "valor total",
        "total da nota",
    )
