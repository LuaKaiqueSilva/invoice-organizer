from io import BytesIO

MAX_OCR_PAGES = 15


def extract_text_with_ocr(pdf_bytes: bytes) -> str:
    """Recognize text from a scanned PDF using optional local OCR dependencies."""
    try:
        import pypdfium2 as pdfium
        import pytesseract
    except ImportError as error:
        raise RuntimeError(
            "Este PDF parece digitalizado. Para usar OCR local, instale as dependências "
            "opcionais de requirements-ocr.txt e o Tesseract OCR."
        ) from error

    try:
        pdf = pdfium.PdfDocument(BytesIO(pdf_bytes))
        if len(pdf) > MAX_OCR_PAGES:
            raise RuntimeError(
                f"O OCR local aceita até {MAX_OCR_PAGES} páginas por documento."
            )
        available_languages = set(pytesseract.get_languages(config=""))
        if "por" not in available_languages:
            raise RuntimeError(
                "O idioma português do Tesseract não está instalado. Instale o pacote "
                "de idioma português e tente novamente."
            )
        language = "por+eng" if "eng" in available_languages else "por"
        page_text = []
        for page in pdf:
            image = page.render(scale=2).to_pil()
            page_text.append(
                pytesseract.image_to_string(
                    image,
                    lang=language,
                    config="--psm 6",
                    timeout=30,
                )
            )
        return "\n".join(page_text).strip()
    except RuntimeError as error:
        if str(error).startswith("O OCR local aceita") or str(error).startswith(
            "O idioma português"
        ):
            raise
        raise RuntimeError(
            "Não foi possível executar o OCR. Confira se o Tesseract e o idioma "
            "português estão instalados."
        ) from error
    except Exception as error:
        raise RuntimeError(
            "Não foi possível executar o OCR. Confira se o Tesseract e o idioma "
            "português estão instalados."
        ) from error
