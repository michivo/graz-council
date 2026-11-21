import argparse
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pymupdf

from graz_merger import read_pdf_folder

DATE_PDF = re.compile(r"^\d{8}\.pdf$", re.IGNORECASE)


@dataclass(frozen=True)
class ImageProcessResult:
    path: Path
    mode: str
    image_count: int
    original_size: int
    final_size: int


def default_pdfs(pdf_folder: Path) -> list[Path]:
    digra_folder = pdf_folder / "digra"
    if not digra_folder.is_dir():
        return []
    return sorted(
        path
        for path in digra_folder.iterdir()
        if path.is_file() and DATE_PDF.fullmatch(path.name)
    )


def document_image_refs(document: pymupdf.Document) -> list[tuple[pymupdf.Page, int]]:
    refs: dict[int, pymupdf.Page] = {}
    for page in document:
        for image in page.get_images(full=True):
            xref = image[0]
            if xref > 0:
                refs.setdefault(xref, page)
    return [(page, xref) for xref, page in refs.items()]


def process_pdf(path: Path, mode: str, quality: int = 75) -> ImageProcessResult:
    if mode not in {"compress", "remove"}:
        raise ValueError("mode must be 'compress' or 'remove'")
    if not 0 <= quality <= 100:
        raise ValueError("quality must be between 0 and 100")
    path = path.resolve()
    original_size = path.stat().st_size
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, suffix=path.suffix
    )
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    try:
        with pymupdf.open(path) as document:
            if document.needs_pass:
                raise RuntimeError(f"PDF is password-protected: {path}")
            images = document_image_refs(document)
            if mode == "remove":
                for page, xref in images:
                    page.delete_image(xref)
            else:
                document.rewrite_images(quality=quality)
            document.save(
                temporary_path,
                garbage=4,
                deflate=True,
                deflate_images=True,
                deflate_fonts=True,
            )
        final_size = temporary_path.stat().st_size
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)
    return ImageProcessResult(
        path=path,
        mode=mode,
        image_count=len(images),
        original_size=original_size,
        final_size=final_size,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compress or remove images in PDF files in place."
    )
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--compress-images",
        action="store_true",
        help="recompress PDF images (default JPEG quality: 75)",
    )
    mode_group.add_argument(
        "--remove-images",
        action="store_true",
        help="replace PDF images with transparent pixels",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=75,
        help="image quality from 0 to 100 for compression (default: 75)",
    )
    parser.add_argument(
        "pdfs",
        nargs="*",
        type=Path,
        help="PDF paths; defaults to YYYYMMDD.pdf files in PDF_FOLDER/digra",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if not 0 <= args.quality <= 100:
        parser.error("--quality must be between 0 and 100")
    mode = "compress" if args.compress_images else "remove"
    pdfs = args.pdfs or default_pdfs(read_pdf_folder())
    if not pdfs:
        print("No matching PDFs found.")
        return

    failures = 0
    for path in pdfs:
        try:
            result = process_pdf(path, mode, args.quality)
            change = result.original_size - result.final_size
            print(
                f"{result.mode}: {result.path.name}: {result.image_count} image(s), "
                f"{result.original_size:,} -> {result.final_size:,} bytes "
                f"({change:+,})"
            )
        except (OSError, RuntimeError, ValueError, pymupdf.FileDataError) as exc:
            failures += 1
            print(f"Failed: {path}: {exc}")
    if failures:
        raise SystemExit(1)