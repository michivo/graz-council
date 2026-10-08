# Graz Council API

Small Flask API for searching the indexed Graz council documents stored in
SQLite. The API exposes a lightweight health check and a full-text search
endpoint backed by SQLite FTS5.

## Requirements

- Python 3.10 or newer
- [`uv`](https://docs.astral.sh/uv/) for environment and dependency
  management
- A populated SQLite database created with the `graz_indexer` tool found in
  this repository

The database must contain an FTS5 table named `fts5_index` with the columns
used by the search query:

- `filename`
- `page`
- `source_url`
- `document_date`
- `document_title`

The database path is configured in [`config.ini`](config.ini) using the
`DATABASE` property. Absolute paths are supported. Relative paths are
resolved relative to `config.ini`, not the directory from which Flask is
started:

```ini
[paths]
DATABASE = db.db
```

The API validates this setting when it starts and exits with a configuration
error if the file is missing, invalid, or does not contain a non-empty
`DATABASE`.

## Setup

From this directory, install the locked dependencies:

```powershell
uv sync
```

## Run the API

Start Flask's development server with:

```powershell
uv run flask --app ./main.py run
```

The server listens on `http://127.0.0.1:5000` by default. To make it
available on another interface or port, use Flask's standard options:

```powershell
uv run flask --app ./main.py run --host 0.0.0.0 --port 8000
```

## Run tests

The unit tests use a temporary SQLite database and do not modify the database
configured for the API:

```powershell
uv run python -m unittest discover -s tests
```

## Endpoints

### `GET /health`

Checks that the Flask application is responding. It does not require a
database connection.

```powershell
curl http://127.0.0.1:5000/health
```

Successful response:

```json
{
  "status": "ok"
}
```

### `GET /health-db`

Verifies that the configured SQLite database can be opened and queried.

```powershell
curl http://127.0.0.1:5000/health-db
```

The response is `{"status":"ok"}` when the database is available, or a
`503` response with `{"status":"db_unavailable"}` when it cannot be reached.

### `GET /search`

Searches the FTS5 index. The `q` parameter is required; `limit` defaults to
`20` and is capped at `100`, while `offset` defaults to `0` and is never
negative.

```powershell
curl "http://127.0.0.1:5000/search?q=budget&limit=10&offset=0"
```

Successful response:

```json
{
  "query": "budget",
  "count": 1,
  "results": [
    {
      "filename": "council-meeting.pdf",
      "page": 4,
      "source_url": "https://example.invalid/council-meeting.pdf",
      "document_date": "2024-01-15",
      "document_title": "Council meeting",
      "snippet": "...approved the <mark>budget</mark>..."
    }
  ]
}
```

If `q` is missing or empty, the API returns `400`:

```json
{
  "error": "Missing query parameter 'q'"
}
```

Search terms are passed as quoted FTS5 phrases so punctuation in user input
does not become FTS5 syntax. Search failures return `400` with an `error`
message.

## Development notes

- The SQLite connection is created lazily per request and closed when the
  Flask application context ends.
- Search results are ordered by SQLite FTS5 rank.
- The API currently has no authentication or write endpoints; keep the
  development server behind an appropriate reverse proxy before exposing it
  publicly.