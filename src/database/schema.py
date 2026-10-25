import sqlite3


def initialize_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            file_name TEXT NOT NULL,
            stored_name TEXT NOT NULL UNIQUE,
            document_type TEXT NOT NULL
                CHECK (document_type IN ('invoice', 'bank_slip', 'other')),
            issuer TEXT,
            document_number TEXT,
            issue_date TEXT,
            due_date TEXT,
            amount TEXT,
            sha256 TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type)"
    )
    connection.commit()
