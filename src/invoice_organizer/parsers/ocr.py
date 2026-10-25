from io import BytesIO

MAX_OCR_PAGES = 5
OCR_RENDER_SCALE = 4
OCR_PAGE_TIMEOUT_SECONDS = 15


class OcrError(RuntimeError):
    """Base class for expected local OCR failures."""


class OcrUnavailableError(OcrError):
    """Optional OCR dependencies or language data are not installed."""


class OcrPageLimitError(OcrError):
    """The document exceeds the OCR page limit."""


class OcrProcessingError(OcrError):
    """The local OCR engine could not process this document."""


def extract_text_with_ocr(pdf_bytes: bytes) -> str:
    """Recognize text from a scanned PDF using optional local OCR dependencies."""
    try:
        import pypdfium2 as pdfium
        import pytesseract
    except ImportError as error:
        raise OcrUnavailableError(
            "Este PDF parece digitalizado. Para usar OCR local, instale as dependências "
            "opcionais de requirements-ocr.txt e o Tesseract OCR."
        ) from error

    try:
        pdf = pdfium.PdfDocument(BytesIO(pdf_bytes))
        if len(pdf) > MAX_OCR_PAGES:
            raise OcrPageLimitError(
                f"O OCR local aceita até {MAX_OCR_PAGES} páginas por documento."
            )
        available_languages = set(pytesseract.get_languages(config=""))
        if "por" not in available_languages:
            raise OcrUnavailableError(
                "O idioma português do Tesseract não está instalado. Instale o pacote "
                "de idioma português e tente novamente."
            )
        language = "por+eng" if "eng" in available_languages else "por"
        page_text = []
        for page in pdf:
            image = page.render(scale=OCR_RENDER_SCALE).to_pil()
            page_text.append(
                pytesseract.image_to_string(
                    image,
                    lang=language,
                    config="--psm 6",
                    timeout=OCR_PAGE_TIMEOUT_SECONDS,
                )
            )
        return "\n".join(page_text).strip()
    except OcrError:
        raise
    except Exception as error:
        raise OcrProcessingError(
            "Não foi possível executar o OCR. Confira se o Tesseract e o idioma "
            "português estão instalados."
        ) from error
