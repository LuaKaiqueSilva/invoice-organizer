import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = Path(
    os.environ.get("INVOICE_ORGANIZER_DATA_DIR", PROJECT_ROOT / "data")
).expanduser()
DATABASE_PATH = DATA_DIR / "invoice_organizer.sqlite3"
DOCUMENTS_DIR = DATA_DIR / "documents"
MAX_PDF_SIZE_BYTES = 15 * 1024 * 1024
