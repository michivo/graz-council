# Graz Council tools

## Configuration

The `graz-fetcher`, `graz-indexer`, and `graz-merger` commands read their local
`configparser` configuration from [`config.ini`](config.ini). Create it by copying
[`config.default.ini`](config.default.ini), then provide absolute paths in
the `[paths]` section:

- `PDF_FOLDER`: the directory containing the downloaded PDF files and their
  metadata JSON files.
- `DATABASE`: the SQLite database file the indexer creates or updates.

`config.ini` is ignored by Git so machine-specific paths are not committed.

## Fetch DiGRA meeting documents

From the `tools` directory, install the tools and fetch the meetings linked from
the Digitales Grazer Rathaus timetable:

```powershell
uv sync
uv run graz-fetcher-digra
```

The command follows the timetable's `Sitzungen` period links and council meeting
pages, including their lazy-loaded tabs and linked document PDFs. Downloads are
saved in `PDF_FOLDER\digra` with the meeting date as an `YYYYMMDD_` filename
prefix. All PDFs found for one meeting date are merged into
`PDF_FOLDER\digra\YYYYMMDD.pdf`.

## Compress or remove PDF images

Choose exactly one image operation. With no PDF paths, the command processes all
`YYYYMMDD.pdf` files directly inside `PDF_FOLDER\digra`:

```powershell
uv run graz-pdf-images --compress-images
uv run graz-pdf-images --remove-images
```

You can provide one or more PDF paths instead. Compression uses PyMuPDF's image
rewriter at quality 75 by default; `--quality` accepts values from 0 to 100.
Each PDF is replaced only after processing and saving succeeds.

## Merge meeting PDFs

From the `tools` directory, install the tools and merge the PDFs:

```powershell
uv sync
uv run graz-merger
```

The merger reads only `PDF_FOLDER`; it does not need a database or metadata
JSON files. It scans PDFs directly in that folder (case-insensitive extension),
not subfolders. Both `YYMMDD` and `YYYYMMDD` filename prefixes are supported
and grouped by calendar day. Two-digit years mean 2000 through 2099.

Results are written to `PDF_FOLDER\merged\YYYYMMDD.pdf`. The destination is
created automatically, and existing daily files are replaced only after a
successful save. Original PDFs are not changed, and reruns do not include
previously merged files.

Each source PDF is preceded by an A4 title page. Titles are derived from
filenames: URL escapes are decoded, underscores become spaces, common German
document names are expanded (such as `antraege` to `Anträge` and `to` to
`Tagesordnung`), and numbered parts become `Teil N`. Trailing revision markers
are removed, so `240215_tagesordnung1v2.pdf` becomes `Tagesordnung Teil 1`.
Other descriptive wording and existing capitalization are preserved.

Invalid date prefixes, missing titles, unreadable PDFs, and password-protected
PDFs are reported as errors, not silently skipped. An error stops the command;
daily outputs completed before the error remain available.

## Tests

```powershell
uv run python -m unittest discover -s tests
```