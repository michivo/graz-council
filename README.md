# Graz Council

Graz Council is a small, local search application for making past decisions,
requests, and protocols from Graz City Council meetings easier to find. It
collects the council's published meeting documents, extracts their text, and
stores the result in a SQLite full-text search index that can be queried
through a lightweight HTTP API and a German-language web interface.

The project is split into three packages:

- [`tools/`](tools/) downloads meeting metadata and optionally PDFs, then
  extracts and indexes PDF content.
- [`api/`](api/) serves the indexed content through a Flask API.
- [`web/`](web/) is a React Router web app with a search page for the API.

## How it works

The data pipeline is:

1. **Fetch** meeting and document metadata from the
   [Graz City Council archive](https://www.graz.at/cms/beitrag/10134085/7768145/Gemeinderat_ArchivNachlese.html).
2. **Download** PDFs when enabled and save the associated metadata as JSON.
3. **Index** each PDF page in SQLite using SQLite FTS5.
4. **Search** the index through the API and follow the source URL to the
   original council document.

Search results include the document title, meeting date, page number, source
URL, and a highlighted text snippet.

## Requirements

- Python 3.10 or newer
- [`uv`](https://docs.astral.sh/uv/) for environment and dependency management
- Internet access when fetching documents from the Graz website

The repository contains separate environments and lock files for the tools and
API. Run commands from the directory whose package you are working with.

## Quick start

### 1. Configure the document tools

Copy the example configuration and fill in paths appropriate for your machine:

```powershell
Copy-Item tools\config.default.ini tools\config.ini
```

Edit `tools\config.ini`:

```ini
[paths]
PDF_FOLDER = C:\data\graz-council\pdfs
DATABASE = C:\data\graz-council\graz-council.db
```

Both paths must be non-empty. `PDF_FOLDER` is used for downloaded PDFs and
their metadata files; `DATABASE` is the SQLite database created by the
indexer. The local configuration file is machine-specific and should not be
committed.

Install the tool dependencies:

```powershell
Set-Location tools
uv sync
```

### 2. Fetch and index the archive

Run the fetcher to collect meeting and document metadata:

```powershell
uv run graz-fetcher
```

The fetcher writes one JSON metadata file per document to `PDF_FOLDER`, along
with `all_metadata.json`. PDF downloading is present in the fetcher but is
disabled by default; enable `export_pdfs` in
[`tools/src/graz_fetcher/__init__.py`](tools/src/graz_fetcher/__init__.py) when
you want the fetch step to download the referenced files as well.

Run the indexer after fetching:

```powershell
uv run graz-indexer
```

The indexer extracts text page by page with PyMuPDF and creates or updates the
SQLite tables used by the API. Every PDF in `PDF_FOLDER` must have a matching
metadata JSON file.

### 3. Configure and run the API

The API needs to point at the same SQLite database. Copy its example
configuration:

```powershell
Copy-Item api\config.default.ini api\config.ini
```

Edit `api\config.ini`:

```ini
[paths]
DATABASE = C:\data\graz-council\graz-council.db
```

Install the API dependencies and start Flask:

```powershell
Set-Location api
uv sync
uv run flask --app .\main.py run
```

The development server listens on `http://127.0.0.1:5000`.

## API examples

Check that the service is running:

```powershell
curl http://127.0.0.1:5000/health
```

Check that the configured database is available:

```powershell
curl http://127.0.0.1:5000/health-db
```

Search for a phrase:

```powershell
curl "http://127.0.0.1:5000/search?q=budget&limit=10&offset=0"
```

Sort by date or restrict to a date range:

```powershell
curl "http://127.0.0.1:5000/search?q=budget&sort=date_desc"
curl "http://127.0.0.1:5000/search?q=budget&date_from=2024-01-01&date_to=2024-12-31"
```

The search endpoint returns JSON in this shape:

```json
{
  "query": "budget",
  "count": 1,
  "results": [
    {
      "filename": "council-meeting.pdf",
      "page": 4,
      "source_url": "https://www.graz.at/...",
      "document_date": "2024-01-15",
      "document_title": "Council meeting",
      "snippet": "...approved the <mark>budget</mark>..."
    }
  ]
}
```

`q` is required. `limit` defaults to 20 and is capped at 100; `offset`
defaults to 0. Search input is treated as a quoted FTS5 phrase, so punctuation
typed by users does not become raw FTS5 syntax. Results can be sorted with
`sort` (`relevance`, `date_asc`, or `date_desc`) and filtered with
`date_from`/`date_to` (`YYYY-MM-DD`, inclusive).

### 4. Run the web interface

The [`web/`](web/) app is a German-language search page that calls the API
above from its server-side loader (no CORS setup required). Point it at the
running API, then start it:

```powershell
Set-Location web
npm install
$env:API_BASE_URL = "http://127.0.0.1:5000"
npm run dev
```

The development server listens on `http://localhost:5173`. See
[`web/README.md`](web/README.md) for build and deployment instructions.

## Development

Run the API unit tests from the API directory:

```powershell
Set-Location api
uv run python -m unittest discover -s tests
```

Useful package-specific documentation:

- [Tool configuration and data processing](tools/README.md)
- [API configuration, endpoints, and tests](api/README.md)
- [Web search interface](web/README.md)

## Project layout

```text
.
├── api/
│   ├── main.py                 # Flask application and search endpoints
│   └── tests/                  # API unit tests
├── tools/
│   └── src/
│       ├── graz_fetcher/       # Archive scraping and document metadata
│       └── graz_indexer/       # PDF extraction and SQLite FTS5 indexing
├── web/
│   └── app/
│       ├── components/         # Search form, results, icons
│       ├── lib/                # Shared types and server-only API client
│       └── routes/home.tsx     # Search page loader and view
└── README.md
```

## Data and limitations

This project uses documents published by the Graz City Council website. The
archive and its document links may change, and downloaded documents are not
part of the source repository. The fetcher currently targets the archive years
defined in its source code, and the API is intended as a local development
service rather than a public production deployment.

The API has no authentication or write endpoints. If it is exposed beyond the
local machine, place it behind an appropriate reverse proxy and review access
controls first.
