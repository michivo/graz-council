import configparser
import sqlite3
from pathlib import Path

from flask import Flask, g, jsonify, request

app = Flask(__name__)
CONFIG_PATH = Path(__file__).parents[0] / "config.ini"
config = configparser.ConfigParser()
if not config.read(CONFIG_PATH, encoding="utf-8"):
    raise RuntimeError(f"Unable to load configuration from {CONFIG_PATH}")

try:
    DB_PATH = config.get("paths", "DATABASE").strip()
except (configparser.NoOptionError, configparser.NoSectionError) as exc:
    raise RuntimeError(
        f"Configuration file {CONFIG_PATH} must define DATABASE in [paths]"
    ) from exc

if not DB_PATH:
    raise RuntimeError(
        f"Configuration file {CONFIG_PATH} must define a non-empty DATABASE value"
    )

def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()

@app.get("/health")
def health():
    try:
        return jsonify(status="ok")
    except sqlite3.Error:
        return jsonify(status="db_unavailable"), 503        

@app.get("/health-db")
def health_db():
    try:
        get_db().execute("SELECT 1").fetchone()
        return jsonify(status="ok")
    except sqlite3.Error:
        return jsonify(status="db_unavailable"), 503

@app.get("/search")
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify(error="Missing query parameter 'q'"), 400

    limit = max(1, min(request.args.get("limit", 20, type=int), 100))
    offset = max(0, request.args.get("offset", 0, type=int))

    # Wrap the input as a quoted FTS5 phrase so user-typed characters
    # like " - * : ( ) don't cause syntax errors.
    fts_query = '"' + q.replace('"', '""') + '"'

    try:
        rows = get_db().execute(
            """
            SELECT filename, page, source_url, document_date, document_title,
                   snippet(fts5_index, 3, '<mark>', '</mark>', '…', 32) AS snippet
            FROM fts5_index
            WHERE fts5_index MATCH ?
            ORDER BY rank
            LIMIT ? OFFSET ?
            """,
            (fts_query, limit, offset),
        ).fetchall()
    except sqlite3.OperationalError as e:
        return jsonify(error="Search failed."), 400

    return jsonify(query=q, count=len(rows), results=[dict(r) for r in rows])