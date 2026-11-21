import tempfile
import unittest
from datetime import date
from pathlib import Path

import pymupdf

from graz_merger import add_title_page, document_date, document_title, merge_pdfs, read_pdf_folder


class FilenameTests(unittest.TestCase):
    def test_date_formats_refer_to_same_day(self):
        for filename in ("231214_antraege2.pdf", "20231214_anfragen.pdf"):
            with self.subTest(filename=filename):
                self.assertEqual(document_date(filename), date(2023, 12, 14))

    def test_short_year_has_explicit_century(self):
        self.assertEqual(document_date("991231_to.pdf"), date(2099, 12, 31))

    def test_invalid_dates_are_rejected(self):
        for filename in ("notes.pdf", "20230229_to.pdf", "230231_to.pdf", "202312141_to.pdf"):
            with self.subTest(filename=filename), self.assertRaises(ValueError):
                document_date(filename)

    def test_titles(self):
        cases = {
            "231214_antraege2.pdf": "Anträge Teil 2",
            "20130125_Tagesordnung%20der%20konstituierenden%20Sitzung_.pdf":
                "Tagesordnung der konstituierenden Sitzung",
            "240215_tagesordnung1v2.pdf": "Tagesordnung Teil 1",
            "240215_tagesordnung_teil2.pdf": "Tagesordnung Teil 2",
            "240215_tagesordnung%201von2.pdf": "Tagesordnung Teil 1",
            "240215_antraege_v2.pdf": "Anträge",
            "240215_dringliche_antraege2.pdf": "Dringliche Anträge Teil 2",
            "240215_Dringlichkeitsantr%C3%A4ge_.pdf": "Dringlichkeitsanträge",
            "240215_to2.pdf": "Tagesordnung Teil 2",
            "240215_anfragen2a.pdf": "Anfragen Teil 2a",
        }
        for filename, title in cases.items():
            with self.subTest(filename=filename):
                self.assertEqual(document_title(filename), title)

    def test_empty_title_is_rejected(self):
        with self.assertRaises(ValueError):
            document_title("240215_.pdf")


class MergerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)

    def make_pdf(self, filename, texts):
        with pymupdf.open() as pdf:
            for text in texts:
                pdf.new_page().insert_text((72, 72), text)
            pdf.save(self.folder / filename)

    def test_grouping_dividers_content_overwrite_and_nonrecursive_scan(self):
        self.make_pdf("231214_antraege2.pdf", ["First source", "Second source page"])
        self.make_pdf("20231214_tagesordnung1v2.PDF", ["Other source"])
        self.make_pdf("240215_anfragen.pdf", ["Different day"])
        (self.folder / "metadata.json").write_text("{}")
        nested = self.folder / "nested"
        nested.mkdir()
        (nested / "not-a-date.pdf").write_text("not scanned")

        outputs = merge_pdfs(self.folder)
        self.assertEqual(
            [path.name for path in outputs], ["20231214.pdf", "20240215.pdf"]
        )
        for _ in range(2):
            with pymupdf.open(outputs[0]) as result:
                self.assertEqual(result.page_count, 5)
                self.assertIn("Tagesordnung Teil 1", result[0].get_text())
                self.assertIn("Other source", result[1].get_text())
                self.assertIn("Anträge Teil 2", result[2].get_text())
                self.assertIn("First source", result[3].get_text())
                self.assertIn("Second source page", result[4].get_text())
            merge_pdfs(self.folder)
        with pymupdf.open(outputs[1]) as result:
            self.assertEqual(result.page_count, 2)
            self.assertIn("Anfragen", result[0].get_text())
        self.assertEqual(len(list((self.folder / "merged").iterdir())), 2)

    def test_corrupt_source_does_not_replace_existing_output(self):
        (self.folder / "231214_antraege.pdf").write_bytes(b"not a PDF")
        destination = self.folder / "merged"
        destination.mkdir()
        output = destination / "20231214.pdf"
        output.write_bytes(b"existing output")
        with self.assertRaisesRegex(RuntimeError, "231214_antraege.pdf"):
            merge_pdfs(self.folder)
        self.assertEqual(output.read_bytes(), b"existing output")
        self.assertEqual(list(destination.iterdir()), [output])

    def test_long_title_wraps_without_losing_text(self):
        title = "Tagesordnung " + "der besonderen Sitzung " * 20
        with pymupdf.open() as pdf:
            add_title_page(pdf, title)
            self.assertEqual(" ".join(pdf[0].get_text().split()), title.strip())

    def test_password_protected_source_is_reported(self):
        source = self.folder / "231214_antraege.pdf"
        with pymupdf.open() as pdf:
            pdf.new_page()
            pdf.save(
                source,
                encryption=pymupdf.PDF_ENCRYPT_AES_256,
                owner_pw="owner",
                user_pw="reader",
            )
        with self.assertRaisesRegex(RuntimeError, "password-protected"):
            merge_pdfs(self.folder)
        self.assertEqual(list((self.folder / "merged").iterdir()), [])

    def test_invalid_filename_is_reported(self):
        (self.folder / "notes.pdf").write_bytes(b"not a PDF")
        with self.assertRaisesRegex(ValueError, "notes.pdf"):
            merge_pdfs(self.folder)

    def test_empty_folder_creates_destination(self):
        self.assertEqual(merge_pdfs(self.folder), [])
        self.assertTrue((self.folder / "merged").is_dir())

    def test_config_needs_only_pdf_folder(self):
        config = self.folder / "config.ini"
        config.write_text(f"[paths]\nPDF_FOLDER = {self.folder}\n", encoding="utf-8")
        self.assertEqual(read_pdf_folder(config), self.folder)

    def test_missing_or_empty_config_is_reported(self):
        config = self.folder / "config.ini"
        with self.assertRaisesRegex(RuntimeError, "Unable to load"):
            read_pdf_folder(config)
        for contents in ("[paths]\n", "[paths]\nPDF_FOLDER = \n", "[other]\nx = y\n"):
            config.write_text(contents)
            with self.subTest(contents=contents), self.assertRaises(RuntimeError):
                read_pdf_folder(config)

    def test_nonexistent_folder_is_reported(self):
        config = self.folder / "config.ini"
        config.write_text(f"[paths]\nPDF_FOLDER = {self.folder / 'absent'}\n")
        with self.assertRaises(NotADirectoryError):
            read_pdf_folder(config)


if __name__ == "__main__":
    unittest.main()
