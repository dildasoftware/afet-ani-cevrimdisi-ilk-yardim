"""
SQLite şeması: chunk metni + normalize edilmiş metin + embedding vektörü,
ve BM25 için bir FTS5 sanal tablosu. Gerçek bir vektör DB değil, SQLite
üzerinde brute-force benzerlik hesaplaması kullanılıyor (bkz. proje planı).
"""
import sqlite3
import json
from typing import List, Optional


def get_connection(db_path: str = "data/afet.db") -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_doc TEXT NOT NULL,
        category TEXT NOT NULL,
        content TEXT NOT NULL,
        normalized_content TEXT NOT NULL,
        chunk_strategy TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_chunks_category ON chunks(category);

    CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
        normalized_content,
        content='chunks',
        content_rowid='id'
    );

    CREATE TABLE IF NOT EXISTS embeddings (
        chunk_id INTEGER PRIMARY KEY,
        vector TEXT NOT NULL,
        FOREIGN KEY (chunk_id) REFERENCES chunks(id)
    );
    """)
    conn.commit()


def insert_chunk(
    conn: sqlite3.Connection,
    source_doc: str,
    category: str,
    content: str,
    normalized_content: str,
    chunk_strategy: str,
    embedding: Optional[List[float]] = None,
) -> int:
    cur = conn.execute(
        "INSERT INTO chunks (source_doc, category, content, normalized_content, chunk_strategy) VALUES (?, ?, ?, ?, ?)",
        (source_doc, category, content, normalized_content, chunk_strategy),
    )
    chunk_id = cur.lastrowid
    conn.execute(
        "INSERT INTO chunks_fts (rowid, normalized_content) VALUES (?, ?)",
        (chunk_id, normalized_content),
    )
    if embedding is not None:
        conn.execute(
            "INSERT INTO embeddings (chunk_id, vector) VALUES (?, ?)",
            (chunk_id, json.dumps(embedding)),
        )
    conn.commit()
    return chunk_id


def count_chunks(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]


def upsert_embedding(conn: sqlite3.Connection, chunk_id: int, embedding: List[float]) -> None:
    """Var olan bir chunk icin embedding ekler veya gunceller."""
    conn.execute(
        "INSERT OR REPLACE INTO embeddings (chunk_id, vector) VALUES (?, ?)",
        (chunk_id, json.dumps(embedding)),
    )
    conn.commit()
