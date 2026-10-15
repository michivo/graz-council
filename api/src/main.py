import configparser
import datetime
import re
import sqlite3
from pathlib import Path

from flask import Flask, g, jsonify, request
from flask_cors import CORS

DATE_FORMAT = "%Y-%m-%d"
SORT_OPTIONS = {
    "relevance": "rank",
    "date_asc": "document_date ASC",
    "date_desc": "document_date DESC",
}
# Matches either a double-quoted phrase or a single whitespace-delimited term.
SEARCH_TERM_PATTERN = re.compile(r'"[^"]*"|\S+')


def parse_date_param(value: str) -> str | None:
    """Validate a date query parameter, returning it unchanged or raising ValueError."""
    datetime.datetime.strptime(value, DATE_FORMAT)
    return value


def build_fts_query(q: str) -> str:
    """Build an FTS5 MATCH expression from a user query with multiple search terms.

    Bare words are treated as individual terms, while double-quoted substrings
    are kept together as exact phrases. All terms/phrases are combined with
    AND so a document must contain every one of them. Each term is quoted so
    user-typed FTS5 syntax characters (e.g. " - * : ( )) don't cause errors.
    """
    terms = []
    for match in SEARCH_TERM_PATTERN.findall(q):
        if match.startswith('"') and match.endswith('"') and len(match) >= 2:
            match = match[1:-1]
        terms.append('"' + match.replace('"', '""') + '"')
    return " AND ".join(terms)

app = Flask(__name__)
CONFIG_PATH = Path(__file__).parents[0] / "../config.ini"
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

# The web client is a client-side rendered SPA, so search requests come
# directly from the browser and the API must allow cross-origin requests.
# Configure allowed origins via `[cors] ALLOWED_ORIGINS` (comma-separated),
# defaulting to "*" since this is a read-only, unauthenticated search API.
try:
    cors_origins = config.get("cors", "ALLOWED_ORIGINS").strip()
except (configparser.NoOptionError, configparser.NoSectionError):
    cors_origins = "*"
origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()] or "*"
CORS(app, resources={r"/*": {"origins": origins}})

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

    sort = request.args.get("sort", "relevance").strip()
    if sort not in SORT_OPTIONS:
        return jsonify(
            error=f"Invalid 'sort' value. Must be one of: {', '.join(SORT_OPTIONS)}"
        ), 400

    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()
    try:
        date_from = parse_date_param(date_from) if date_from else None
        date_to = parse_date_param(date_to) if date_to else None
    except ValueError:
        return jsonify(error="Invalid date format. Use YYYY-MM-DD."), 400

    # Support multiple search terms: bare words are ANDed together, while
    # "quoted phrases" are kept intact as a single exact phrase.
    fts_query = build_fts_query(q)

    conditions = ["fts5_index MATCH ?"]
    params: list = [fts_query]
    if date_from:
        conditions.append("document_date >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("document_date <= ?")
        params.append(date_to)
    where_clause = " AND ".join(conditions)

    try:
        db = get_db()
        total = db.execute(
            f"SELECT COUNT(*) FROM fts5_index WHERE {where_clause}",
            params,
        ).fetchone()[0]
        rows = db.execute(
            f"""
            SELECT filename, page, source_url, document_date, document_title,
                   snippet(fts5_index, 3, '<mark>', '</mark>', '…', 32) AS snippet
            FROM fts5_index
            WHERE {where_clause}
            ORDER BY {SORT_OPTIONS[sort]}
            LIMIT ? OFFSET ?
            """,
            [*params, limit, offset],
        ).fetchall()
    except sqlite3.OperationalError:
        app.logger.exception("Search query failed: q=%r sort=%r", q, sort)
        return jsonify(error="Search failed."), 400

    return jsonify(
        query=q, count=len(rows), total=total, results=[dict(r) for r in rows]
    )