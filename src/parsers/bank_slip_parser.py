from src.parsers.base_parser import BaseParser


class BankSlipParser(BaseParser):
    document_type = "bank_slip"
    issuer_labels = ("beneficiário", "beneficiario", "cedente", "fornecedor")
    number_labels = (
        "nosso número",
        "nosso numero",
        "número do documento",
        "numero do documento",
    )
    amount_labels = (
        "valor do documento",
        "valor cobrado",
        "valor a pagar",
        "valor do boleto",
        "valor",
    )
