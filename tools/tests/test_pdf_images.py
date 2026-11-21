import tempfile
import unittest
from pathlib import Path

import pymupdf

from graz_pdf_images import default_pdfs, process_pdf


class PdfImageToolTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)

    def make_image_pdf(self, path):
        pixmap = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 80, 80), False)
        pixmap.clear_with(120)
        with pymupdf.open() as document:
            page = document.new_page(width=200, height=200)
            page.insert_image(pymupdf.Rect(40, 40, 160, 160), pixmap=pixmap)
            document.save(path)

    def test_default_pdfs_matches_only_date_named_files_in_digra(self):
        digra = self.folder / "digra"
        digra.mkdir()
        expected = digra / "20260827.pdf"
        expected.write_bytes(b"pdf")
        (digra / "agenda.pdf").write_bytes(b"pdf")
        (digra / "2026082.pdf").write_bytes(b"pdf")
        (digra / "20260828.PDF").write_bytes(b"pdf")
        nested = digra / "nested"
        nested.mkdir()
        (nested / "20260829.pdf").write_bytes(b"pdf")

        self.assertEqual(
            default_pdfs(self.folder), [expected, digra / "20260828.PDF"]
        )

    def test_remove_images_replaces_visible_image_in_place(self):
        source = self.folder / "20260827.pdf"
        self.make_image_pdf(source)

        result = process_pdf(source, "remove")

        self.assertEqual(result.image_count, 1)
        self.assertEqual(result.path, source.resolve())
        self.assertTrue(source.is_file())
        with pymupdf.open(source) as document:
            self.assertEqual(document.page_count, 1)
            self.assertEqual(document[0].get_pixmap().pixel(100, 100), (255, 255, 255))

    def test_compress_images_rewrites_and_keeps_pdf_valid(self):
        source = self.folder / "20260827.pdf"
        self.make_image_pdf(source)
        original_size = source.stat().st_size

        result = process_pdf(source, "compress", quality=75)

        self.assertEqual(result.image_count, 1)
        self.assertLess(source.stat().st_size, original_size)
        with pymupdf.open(source) as document:
            self.assertEqual(document.page_count, 1)
            self.assertTrue(document[0].get_images(full=True))

    def test_failure_leaves_original_file_unchanged(self):
        source = self.folder / "broken.pdf"
        original = b"not a PDF"
        source.write_bytes(original)

        with self.assertRaises((pymupdf.FileDataError, RuntimeError)):
            process_pdf(source, "remove")

        self.assertEqual(source.read_bytes(), original)
        self.assertEqual(list(self.folder.iterdir()), [source])

    def test_invalid_mode_and_quality_are_rejected(self):
        source = self.folder / "20260827.pdf"
        self.make_image_pdf(source)
        for mode, quality in (("other", 75), ("compress", 101)):
            with self.subTest(mode=mode, quality=quality), self.assertRaises(ValueError):
                process_pdf(source, mode, quality)


if __name__ == "__main__":
    unittest.main()