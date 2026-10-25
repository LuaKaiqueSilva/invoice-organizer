import os
import re
import tempfile
from pathlib import Path


def clean_display_filename(filename: str) -> str:
    basename = filename.replace("\\", "/").rsplit("/", maxsplit=1)[-1]
    cleaned = re.sub(r"[\x00-\x1f\x7f]", "", basename).strip()
    return (cleaned or "documento.pdf")[:180]


def save_pdf_safely(content: bytes, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        os.chmod(destination.parent, 0o700)
    except OSError:
        pass
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=".upload-", suffix=".tmp", dir=destination.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(file_descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary_path, 0o600)
        temporary_path.replace(destination)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
