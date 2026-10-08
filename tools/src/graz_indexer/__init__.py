import configparser
import datetime
import json
import os
import sqlite3
from pathlib import Path

import pymupdf  # PyMuPDF

CONFIG_PATH = Path(__file__).parents[2] / "config.ini"
METADATA_KEYS = ["filename", "page", "text", "source_url", "document_date", "document_title"]

config = configparser.ConfigParser()
if not config.read(CONFIG_PATH, encoding="utf-8"):
    raise RuntimeError(f"Unable to load configuration from {CONFIG_PATH}")

try:
    PDF_FOLDER = config.get("paths", "PDF_FOLDER").strip()
    DATABASE = config.get("paths", "DATABASE").strip()
except (configparser.NoOptionError, configparser.NoSectionError) as exc:
    raise RuntimeError(
        f"Configuration file {CONFIG_PATH} must define PDF_FOLDER and DATABASE in [paths]"
    ) from exc

if not PDF_FOLDER or not DATABASE:
    raise RuntimeError(
        f"Configuration file {CONFIG_PATH} must define non-empty PDF_FOLDER and DATABASE values"
    )


def main() -> None:
    # Create or connect to SQLite database
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    create_database(cursor)

    # Process all PDFs in the folder
    for filename in os.listdir(PDF_FOLDER):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(PDF_FOLDER, filename)
            metadata_path = os.path.splitext(pdf_path)[0] + ".json"
            extracted_data, metadata = extract_pdf_metadata(pdf_path, metadata_path)

            for item in extracted_data:
                cursor.execute("""
                INSERT INTO indexed_files (filename, page, text, source_url, document_date, document_title)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (item["filename"], item["page"], item["text"], item["source_url"], metadata["document_date"], metadata["document_title"]))

                # Index only the row we just inserted, not the whole table again
                new_id = cursor.lastrowid
                cursor.execute("""
                INSERT INTO fts5_index (id, filename, page, text, source_url, document_date, document_title)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (new_id, item["filename"], item["page"], item["text"], item["source_url"], metadata["document_date"], metadata["document_title"]))

            print(f"Indexed {filename}")

    # Commit changes and close connection
    conn.commit()
    conn.close()

    print("Indexed database created successfully.")

def create_database(cursor: sqlite3.Cursor) -> None:

    # Create FTS5 table for search indexing
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS indexed_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        page INTEGER,
        text TEXT,
        source_url TEXT,
        document_date TEXT,
        document_title TEXT,
        MATCHED TEXT
    )
    """)

    # Create FTS5 index on the text column for full-text search
    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS fts5_index USING fts5(
        id,
        filename,
        page,
        text,
        source_url,
        document_date,
        document_title,
        MATCHED
    )
    """)

# Function to extract text and metadata from a PDF
def extract_pdf_metadata(pdf_path: str, metadata_path: str) -> tuple[list[dict], dict]:
    doc = pymupdf.open(pdf_path)
    stored_metadata = None
    with open(metadata_path) as f:
        stored_metadata = json.load(f)
    metadata = {
        "filename": os.path.basename(pdf_path),
        "source_url": stored_metadata["pdf_url"] if stored_metadata and "pdf_url" in stored_metadata else "file://" + pdf_path,
        "document_date": stored_metadata["date"] if stored_metadata and "document_date" in stored_metadata else datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "document_title": stored_metadata["document_title"] if stored_metadata and "document_title" in stored_metadata else os.path.splitext(os.path.basename(pdf_path))[0]
    }

    extracted_text = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        extracted_text.append({
            "page": page_num + 1,
            "text": text,
            "filename": os.path.basename(pdf_path),
            "source_url": metadata["source_url"],
            "document_date": metadata["document_date"],
            "document_title": metadata["document_title"]
        })

    return extracted_text, metadata
