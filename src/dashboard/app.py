import csv
import io
import logging
import sqlite3
from decimal import Decimal

import streamlit as st

from src.config.settings import MAX_PDF_SIZE_BYTES
from src.demo import build_demo_documents
from src.models.document import Document
from src.services.document_service import DocumentService
from src.services.exceptions import DocumentImportError, DuplicateDocumentError

TYPE_LABELS = {
    "invoice": "Nota fiscal",
    "bank_slip": "Boleto",
    "other": "Outro / não identificado",
}
logger = logging.getLogger(__name__)


@st.cache_resource
def get_document_service() -> DocumentService:
    return DocumentService()


def format_amount(amount: Decimal | None) -> str:
    if amount is None:
        return "Não identificado"
    formatted = f"{amount:,.2f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def to_csv(documents: list[Document]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["Arquivo", "Tipo", "Emitente/beneficiário", "Número", "Emissão", "Vencimento", "Valor", "Importado em"]
    )
    for document in documents:
        writer.writerow(
            [
                csv_safe_cell(document.file_name),
                csv_safe_cell(TYPE_LABELS.get(document.document_type, document.document_type)),
                csv_safe_cell(document.issuer or ""),
                csv_safe_cell(document.document_number or ""),
                document.issue_date or "",
                document.due_date or "",
                str(document.amount) if document.amount is not None else "",
                document.created_at.isoformat(timespec="seconds"),
            ]
        )
    return output.getvalue()


def csv_safe_cell(value: str) -> str:
    """Prevent untrusted PDF text from being interpreted as a spreadsheet formula."""

    if value.startswith(("=", "+", "-", "@", "\t", "\r")):
        return f"'{value}"
    return value


def main() -> None:
    st.set_page_config(page_title="Organizador de Notas e Boletos", page_icon="🧾", layout="wide")
    st.title("🧾 Organizador de Notas e Boletos")
    st.caption("Guarde PDFs localmente e encontre os dados principais em um só lugar.")

    with st.sidebar:
        st.header("Configurações")
        demo_mode = st.toggle("Modo de demonstração", value=True, key="demo_mode")
        st.caption("Seus arquivos e o banco de dados permanecem na pasta local data/.")

    if demo_mode:
        st.info("Modo de demonstração: os dados abaixo são fictícios e não são salvos.")

    with st.expander("Importar documento PDF", expanded=not demo_mode):
        st.write("Aceita PDFs com texto selecionável de até 15 MB. Documentos escaneados ainda não têm OCR.")
        selected_type_label = st.selectbox(
            "Tipo do documento",
            ("Detectar automaticamente", "Nota fiscal", "Boleto", "Outro"),
            disabled=demo_mode,
        )
        selected_type = {
            "Detectar automaticamente": "auto",
            "Nota fiscal": "invoice",
            "Boleto": "bank_slip",
            "Outro": "other",
        }[selected_type_label]
        uploaded_file = st.file_uploader(
            "Escolha um arquivo PDF",
            type=["pdf"],
            disabled=demo_mode,
            help=f"Tamanho máximo: {MAX_PDF_SIZE_BYTES // (1024 * 1024)} MB.",
        )
        if st.button("Importar PDF", type="primary", disabled=demo_mode or uploaded_file is None):
            try:
                document = get_document_service().import_pdf(
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    selected_type,
                )
                st.session_state["import_notice"] = (
                    f"{document.file_name} importado. Confira os campos extraídos abaixo."
                )
                st.rerun()
            except DuplicateDocumentError as error:
                st.warning(str(error))
            except DocumentImportError as error:
                st.error(str(error))
            except (OSError, sqlite3.Error):
                logger.exception("Document import failed")
                st.error("Não foi possível importar o documento. Verifique o arquivo e tente novamente.")

    notice = st.session_state.pop("import_notice", None)
    if notice:
        st.success(notice)
        st.caption("Confira os dados extraídos com o PDF original antes de usá-los.")

    documents = build_demo_documents() if demo_mode else get_document_service().list_documents()
    invoice_count = sum(document.document_type == "invoice" for document in documents)
    bank_slip_count = sum(document.document_type == "bank_slip" for document in documents)
    col_docs, col_invoices, col_slips = st.columns(3)
    col_docs.metric("Documentos", len(documents))
    col_invoices.metric("Notas fiscais", invoice_count)
    col_slips.metric("Boletos", bank_slip_count)

    st.subheader("Documentos salvos")
    search_col, type_col = st.columns([3, 1])
    with search_col:
        search = st.text_input("Pesquisar", placeholder="Nome do arquivo, emitente ou número")
    with type_col:
        type_filter = st.selectbox(
            "Filtrar por tipo",
            ("Todos", "Nota fiscal", "Boleto", "Outro / não identificado"),
        )

    filtered = documents
    if search:
        query = search.casefold()
        filtered = [
            document
            for document in filtered
            if query
            in " ".join(
                value
                for value in (document.file_name, document.issuer, document.document_number)
                if value
            ).casefold()
        ]
    if type_filter != "Todos":
        selected_key = next(key for key, label in TYPE_LABELS.items() if label == type_filter)
        filtered = [document for document in filtered if document.document_type == selected_key]

    if filtered:
        rows = [
            {
                "Arquivo": document.file_name,
                "Tipo": TYPE_LABELS.get(document.document_type, document.document_type),
                "Emitente / beneficiário": document.issuer or "—",
                "Número": document.document_number or "—",
                "Vencimento": document.due_date or "—",
                "Valor": format_amount(document.amount),
            }
            for document in filtered
        ]
        st.dataframe(rows, hide_index=True, width="stretch")
        st.download_button(
            "Exportar lista filtrada como CSV",
            data=to_csv(filtered),
            file_name="documentos.csv",
            mime="text/csv",
        )
        document_options = {
            f"{document.file_name} — {TYPE_LABELS.get(document.document_type, document.document_type)} ({document.id[:6]})": document
            for document in filtered
        }
        selected_label = st.selectbox("Abrir documento", tuple(document_options))
        selected_document = document_options[selected_label]
        details_col, file_col = st.columns([3, 1])
        with details_col:
            st.markdown(f"**Emitente / beneficiário:** {selected_document.issuer or 'Não identificado'}")
            st.markdown(f"**Número:** {selected_document.document_number or 'Não identificado'}")
            st.markdown(f"**Data de emissão:** {selected_document.issue_date or 'Não identificada'}")
            st.markdown(f"**Vencimento:** {selected_document.due_date or 'Não identificado'}")
            st.markdown(f"**Valor:** {format_amount(selected_document.amount)}")
        with file_col:
            if not demo_mode:
                pdf = get_document_service().get_pdf_bytes(selected_document.id)
                if pdf:
                    st.download_button(
                        "Baixar PDF original",
                        data=pdf[1],
                        file_name=pdf[0],
                        mime="application/pdf",
                    )
    else:
        st.info(
            "Nenhum documento nesta lista. Ative o Modo de demonstração para ver exemplos fictícios, "
            "ou importe um PDF acima."
        )

    st.divider()
    st.caption(
        "A extração automática pode falhar conforme o layout do documento. "
        "Confira os valores no PDF original."
    )
