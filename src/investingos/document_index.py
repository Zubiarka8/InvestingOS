"""Local incremental full-text search over extracted source documents."""
import re
import sqlite3
from pathlib import Path

from .knowledge_tools import _hash


def _database_path(project_path, project):
    return Path(project_path).resolve().parent / f".InvestingOS-{project['id']}.sqlite3"


def _connect(path, *, rebuild=False):
    connection = sqlite3.connect(path)
    try:
        if rebuild:
            connection.execute("DROP TABLE IF EXISTS document_fts")
            connection.execute("DROP TABLE IF EXISTS indexed_files")
        connection.execute("CREATE TABLE IF NOT EXISTS indexed_files (source_id TEXT PRIMARY KEY, path TEXT NOT NULL, digest TEXT NOT NULL, title TEXT NOT NULL, rowid INTEGER NOT NULL)")
        connection.execute("CREATE VIRTUAL TABLE IF NOT EXISTS document_fts USING fts5(source_id UNINDEXED, title, content, tokenize='unicode61')")
        connection.commit()
        return connection
    except sqlite3.OperationalError as exc:
        connection.close()
        if "fts5" in str(exc).lower() or "no such module" in str(exc).lower():
            raise ValueError("this Python SQLite build does not include FTS5 full-text search") from exc
        raise


def index_documents(project_path, project, *, rebuild=False):
    database = _database_path(project_path, project)
    connection = _connect(database, rebuild=rebuild)
    report = {"indexed": [], "unchanged": [], "missing": [], "failed": []}
    active_ids = set()
    try:
        for source in project.get("sources", []):
            path_value = source.get("extracted_path")
            if not path_value:
                continue
            source_id = source["id"]
            active_ids.add(source_id)
            path = Path(path_value)
            if not path.is_file():
                report["missing"].append({"source_id": source_id, "path": str(path)})
                stale = connection.execute("SELECT rowid FROM indexed_files WHERE source_id=?", (source_id,)).fetchone()
                if stale:
                    connection.execute("DELETE FROM document_fts WHERE rowid=?", (stale[0],))
                    connection.execute("DELETE FROM indexed_files WHERE source_id=?", (source_id,))
                    connection.commit()
                continue
            try:
                digest = _hash(path)
                old = connection.execute(
                    "SELECT path, digest, title, rowid FROM indexed_files WHERE source_id=?", (source_id,)
                ).fetchone()
                title = source.get("title", path.name)
                if not rebuild and old and old[:3] == (str(path), digest, title):
                    report["unchanged"].append(source_id)
                    continue
                content = path.read_text(encoding="utf-8")
                rowid = old[3] if old else None
                if old:
                    connection.execute("DELETE FROM document_fts WHERE rowid=?", (rowid,))
                cursor = connection.execute(
                    "INSERT INTO document_fts(source_id, title, content) VALUES (?, ?, ?)",
                    (source_id, title, content),
                )
                rowid = cursor.lastrowid
                connection.execute(
                    "INSERT INTO indexed_files(source_id, path, digest, title, rowid) VALUES (?, ?, ?, ?, ?) "
                    "ON CONFLICT(source_id) DO UPDATE SET path=excluded.path, digest=excluded.digest, "
                    "title=excluded.title, rowid=excluded.rowid",
                    (source_id, str(path), digest, title, rowid),
                )
                connection.commit()
                report["indexed"].append(source_id)
            except (OSError, UnicodeError, sqlite3.Error) as exc:
                connection.rollback()
                report["failed"].append({"source_id": source_id, "error": str(exc)})

        indexed_ids = {row[0] for row in connection.execute("SELECT source_id FROM indexed_files")}
        for stale_id in indexed_ids - active_ids:
            row = connection.execute("SELECT rowid FROM indexed_files WHERE source_id=?", (stale_id,)).fetchone()
            connection.execute("DELETE FROM document_fts WHERE rowid=?", (row[0],))
            connection.execute("DELETE FROM indexed_files WHERE source_id=?", (stale_id,))
        connection.commit()
    finally:
        connection.close()
    report["database"] = str(database)
    return report


def search_documents(project_path, project, query, *, limit=20):
    if not isinstance(query, str) or not query.strip() or not 1 <= limit <= 100:
        raise ValueError("provide a query and a limit between 1 and 100")
    tokens = re.findall(r"[\w-]+", query, flags=re.UNICODE)
    if not tokens:
        raise ValueError("query must contain at least one searchable word")
    expression = " AND ".join('"' + token.replace('"', '""') + '"' for token in tokens)
    database = _database_path(project_path, project)
    if not database.is_file():
        raise ValueError("document index not found; run index-documents first")
    connection = _connect(database)
    try:
        rows = connection.execute(
            "SELECT document_fts.source_id, document_fts.title, indexed_files.path, "
            "snippet(document_fts, 2, '[', ']', '…', 16) "
            "FROM document_fts JOIN indexed_files USING(source_id) "
            "WHERE document_fts MATCH ? ORDER BY bm25(document_fts) LIMIT ?",
            (expression, limit),
        ).fetchall()
    except sqlite3.OperationalError as exc:
        raise ValueError(f"document search failed: {exc}") from exc
    finally:
        connection.close()
    return [{"source_id": row[0], "title": row[1], "path": row[2], "snippet": row[3]} for row in rows]
