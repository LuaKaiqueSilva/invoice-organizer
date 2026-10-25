import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from invoice_organizer.config.settings import DATABASE_PATH
from invoice_organizer.database.schema import initialize_schema


@contextmanager
def get_connection(database_path: Path = DATABASE_PATH) -> Iterator[sqlite3.Connection]:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=10)
    if os.name != "nt":
        try:
            os.chmod(database_path, 0o600)
        except OSError:
            pass
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        initialize_schema(connection)
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
