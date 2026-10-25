import hashlib
import uuid
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from src.config.settings import DOCUMENTS_DIR, MAX_PDF_SIZE_BYTES
from src.models.document import Document
from src.parsers.parser_factory import DocumentParseError, ParserFactory
from src.repositories.document_repository import DocumentRepository
from src.services.exceptions import DocumentImportError, DuplicateDocumentError
from src.utils.file_utils import clean_display_filename, save_pdf_safely


class DocumentService:
    def __init__(
        self,
        repository: DocumentRepository | None = None,
        documents_dir: Path = DOCUMENTS_DIR,
        max_size_bytes: int = MAX_PDF_SIZE_BYTES,
        parser_factory: type[ParserFactory] = ParserFactory,
    ) -> None:
        self.repository = repository or DocumentRepository()
        self.documents_dir = documents_dir
        self.max_size_bytes = max_size_bytes
        self.parser_factory = parser_factory

    def import_pdf(self, file_name: str, content: bytes, selected_type: str = "auto") -> Document:
        if selected_type not in {"auto", "invoice", "bank_slip", "other"}:
            raise DocumentImportError("Selecione um tipo de documento válido.")
        display_name = clean_display_filename(file_name)
        if Path(display_name).suffix.lower() != ".pdf":
            raise DocumentImportError("Selecione um arquivo com extensão .pdf.")
        if not content:
            raise DocumentImportError("O arquivo está vazio.")
        if len(content) > self.max_size_bytes:
            limit_mb = self.max_size_bytes // (1024 * 1024)
            raise DocumentImportError(f"O PDF excede o limite de {limit_mb} MB.")
        if b"%PDF-" not in content[:1024]:
            raise DocumentImportError("O arquivo selecionado não parece ser um PDF válido.")

        digest = hashlib.sha256(content).hexdigest()
        if self.repository.get_by_hash(digest):
            raise DuplicateDocumentError("Este mesmo PDF já foi importado.")

        try:
            parsed = self.parser_factory.parse_pdf(content, selected_type)
        except (DocumentParseError, ValueError) as error:
            raise DocumentImportError(str(error)) from error

        document_id = uuid.uuid4().hex
        stored_name = f"{document_id}.pdf"
        destination = self.documents_dir / stored_name
        document = Document(
            id=document_id,
            file_name=display_name,
            stored_name=stored_name,
            document_type=parsed.document_type,
            issuer=parsed.issuer,
            document_number=parsed.document_number,
            issue_date=parsed.issue_date,
            due_date=parsed.due_date,
            amount=parsed.amount,
            sha256=digest,
            created_at=datetime.now(),
            extraction_method=parsed.extraction_method,
        )

        save_pdf_safely(content, destination)
        try:
            self.repository.add(document)
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        return document

    def list_documents(self) -> list[Document]:
        return self.repository.list_all()

    def get_pdf_bytes(self, document_id: str) -> tuple[str, bytes] | None:
        document = self.repository.get_by_id(document_id)
        if not document:
            return None
        stored_name = Path(document.stored_name)
        if stored_name.name != document.stored_name or stored_name.suffix.lower() != ".pdf":
            raise DocumentImportError("O caminho do documento armazenado é inválido.")
        path = self.documents_dir / stored_name
        return document.file_name, path.read_bytes()

    def update_metadata(
        self,
        document_id: str,
        issuer: str,
        document_number: str,
        issue_date: str,
        due_date: str,
        amount: str,
    ) -> Document:
        def clean_text(value: str) -> str | None:
            cleaned = value.strip()
            if len(cleaned) > 250:
                raise DocumentImportError("Os campos de texto devem ter até 250 caracteres.")
            return cleaned or None

        def clean_date(value: str) -> str | None:
            cleaned = value.strip()
            if not cleaned:
                return None
            try:
                return date.fromisoformat(cleaned).isoformat()
            except ValueError as error:
                raise DocumentImportError("Informe as datas no formato AAAA-MM-DD.") from error

        cleaned_amount = amount.strip().replace("R$", "").replace(" ", "")
        if "," in cleaned_amount:
            cleaned_amount = cleaned_amount.replace(".", "").replace(",", ".")
        try:
            parsed_amount = Decimal(cleaned_amount) if cleaned_amount else None
            if parsed_amount is not None and not parsed_amount.is_finite():
                raise InvalidOperation
        except InvalidOperation as error:
            raise DocumentImportError("Informe um valor válido, por exemplo 123,45.") from error

        updated = self.repository.update_metadata(
            document_id,
            clean_text(issuer),
            clean_text(document_number),
            clean_date(issue_date),
            clean_date(due_date),
            parsed_amount,
        )
        if updated is None:
            raise DocumentImportError("Este documento não foi encontrado.")
        return updated

    def delete_document(self, document_id: str) -> bool:
        document = self.repository.delete(document_id)
        if document is None:
            return False
        stored_name = Path(document.stored_name)
        if stored_name.name == document.stored_name and stored_name.suffix.lower() == ".pdf":
            (self.documents_dir / stored_name).unlink(missing_ok=True)
        return True
