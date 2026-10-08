# Graz Council tools

## Configuration

The `graz-fetcher` and `graz-indexer` commands read their local
`configparser` configuration from [`config.json`](config.json). Create it by copying
[`config.default.json`](config.default.json), then provide absolute paths in
the `[paths]` section:

- `PDF_FOLDER`: the directory containing the downloaded PDF files and their
  metadata JSON files.
- `DATABASE`: the SQLite database file the indexer creates or updates.

`config.json` is ignored by Git so machine-specific paths are not committed.