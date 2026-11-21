import configparser
import re
import tempfile
from datetime import date
from pathlib import Path
from urllib.parse import unquote

import pymupdf

CONFIG_PATH = Path(__file__).parents[2] / "config.ini"
PREFIX = re.compile(r"^([0-9]{8}|[0-9]{6})(?![0-9])[_ -]*(.*)$")
TITLE_WORDS = {
    "antraege": "Anträge",
    "antrag": "Antrag",
    "anfragen": "Anfragen",
    "anfrage": "Anfrage",
    "anwesenheitsliste": "Anwesenheitsliste",
    "dringlichkeitsantraege": "Dringlichkeitsanträge",
    "fragestunde": "Fragestunde",
    "mitteilungen": "Mitteilungen",
    "nachrufe": "Nachrufe",
    "tagesordnung": "Tagesordnung",
    "to": "Tagesordnung",
    "teil": "Teil",
    "buerger": "Bürger",
    "stadtraete": "Stadträte",
}


def read_pdf_folder(config_path: Path = CONFIG_PATH) -> Path:
    config = configparser.ConfigParser(interpolation=None)
    if not config.read(config_path, encoding="utf-8"):
        raise RuntimeError(f"Unable to load configuration from {config_path}")
    try:
        folder = config.get("paths", "PDF_FOLDER").strip()
    except (configparser.NoOptionError, configparser.NoSectionError) as exc:
        raise RuntimeError(
            f"Configuration file {config_path} must define PDF_FOLDER in [paths]"
        ) from exc
    if not folder:
        raise RuntimeError(
            f"Configuration file {config_path} must define a non-empty PDF_FOLDER value"
        )
    path = Path(folder)
    if not path.is_dir():
        raise NotADirectoryError(f"PDF_FOLDER is not an existing directory: {path}")
    return path


def document_date(filename: str) -> date:
    match = PREFIX.fullmatch(Path(filename).stem)
    if not match:
        raise ValueError(f"PDF filename must start with YYMMDD or YYYYMMDD: {filename}")
    prefix = match[1]
    # Two-digit archive years consistently refer to the twenty-first century.
    if len(prefix) == 6:
        prefix = "20" + prefix
    try:
        return date(int(prefix[:4]), int(prefix[4:6]), int(prefix[6:8]))
    except ValueError as exc:
        raise ValueError(f"Invalid date prefix in PDF filename: {filename}") from exc


def document_title(filename: str) -> str:
    match = PREFIX.fullmatch(Path(filename).stem)
    if not match:
        raise ValueError(f"PDF filename must start with YYMMDD or YYYYMMDD: {filename}")
    title = unquote(match[2]).replace("_", " ").strip(" -")
    # A trailing v2 is a revision, whereas 1v2 / 1von2 denotes part 1 of 2.
    title = re.sub(r"(?i)v[0-9]+$", "", title).rstrip()
    title = re.sub(r"(?i)([0-9]+)\s*von\s*[0-9]+$", r"\1", title)
    title = re.sub(r"(?i)\bteil\s*([0-9]+)", r"Teil \1", title)
    title = re.sub(r"(?i)(?<![0-9])([0-9]+)([a-z]?)$", r" Teil \1\2", title)
    title = re.sub(r"(?i)\bteil\s+teil\b", "Teil", title)
    title = re.sub(
        r"[^\W\d_]+",
        lambda word: TITLE_WORDS.get(word[0].lower(), word[0]),
        title,
    )
    title = " ".join(title.split())
    if not title:
        raise ValueError(f"PDF filename has no document title: {filename}")
    return title[0].upper() + title[1:]


def add_title_page(document: pymupdf.Document, title: str) -> None:
    page = document.new_page(width=595, height=842)
    box = pymupdf.Rect(50, 200, 545, 742)
    for size in range(28, 9, -1):
        if page.insert_textbox(box, title, fontsize=size, fontname="helv", align=1) >= 0:
            return
    raise ValueError(f"Document title is too long to fit on a divider page: {title}")


def merge_day(paths: list[Path], output: Path) -> None:
    with pymupdf.open() as merged:
        for path in paths:
            try:
                with pymupdf.open(path) as source:
                    if source.needs_pass:
                        raise ValueError("PDF is password-protected")
                    if not source.page_count:
                        raise ValueError("PDF contains no pages")
                    add_title_page(merged, document_title(path.name))
                    merged.insert_pdf(source)
            except (RuntimeError, ValueError, OSError) as exc:
                raise RuntimeError(f"Unable to merge {path}: {exc}") from exc
        # Replace only after a complete save, preserving an old output on failure.
        with tempfile.NamedTemporaryFile(dir=output.parent, suffix=".pdf", delete=False) as temp:
            temporary_path = Path(temp.name)
        try:
            merged.save(temporary_path, garbage=4, deflate=True)
            temporary_path.replace(output)
        finally:
            temporary_path.unlink(missing_ok=True)


def merge_pdfs(folder: Path) -> list[Path]:
    groups: dict[date, list[Path]] = {}
    for path in sorted(folder.iterdir()):
        if path.is_file() and path.suffix.lower() == ".pdf":
            day = document_date(path.name)
            groups.setdefault(day, []).append(path)

    destination = folder / "merged"
    destination.mkdir(exist_ok=True)
    outputs = []
    for day, paths in sorted(groups.items()):
        output = destination / f"{day:%Y%m%d}.pdf"
        merge_day(paths, output)
        outputs.append(output)
        print(f"Merged {len(paths)} PDF(s) into {output}")
    return outputs


def main() -> None:
    outputs = merge_pdfs(read_pdf_folder())
    print(f"Created {len(outputs)} merged PDF(s).")
