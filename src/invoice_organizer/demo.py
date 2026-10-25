from datetime import datetime, timedelta
from decimal import Decimal

from invoice_organizer.models.document import Document


def build_demo_documents() -> list[Document]:
    now = datetime.now().replace(microsecond=0)
    return [
        Document(
            id="demo-invoice-1",
            file_name="nota-fiscal-exemplo.pdf",
            stored_name="",
            document_type="invoice",
            issuer="Comércio Exemplo Ltda.",
            document_number="NF 1042",
            issue_date=(now - timedelta(days=8)).date().isoformat(),
            due_date=None,
            amount=Decimal("1299.90"),
            sha256="demo-invoice-sha256",
            created_at=now - timedelta(days=8),
        ),
        Document(
            id="demo-slip-1",
            file_name="boleto-exemplo.pdf",
            stored_name="",
            document_type="bank_slip",
            issuer="Fornecedor Exemplo S.A.",
            document_number="DOC 8831",
            issue_date=None,
            due_date=(now + timedelta(days=4)).date().isoformat(),
            amount=Decimal("349.90"),
            sha256="demo-slip-sha256",
            created_at=now - timedelta(days=2),
        ),
        Document(
            id="demo-slip-2",
            file_name="boleto-internet-exemplo.pdf",
            stored_name="",
            document_type="bank_slip",
            issuer="Serviços Exemplo Ltda.",
            document_number="DOC 1902",
            issue_date=None,
            due_date=(now + timedelta(days=12)).date().isoformat(),
            amount=Decimal("119.90"),
            sha256="demo-slip-2-sha256",
            created_at=now - timedelta(days=1),
        ),
    ]
