import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

import pymupdf
from bs4 import BeautifulSoup

from graz_fetcher_digra import (
    DownloadLink,
    meeting_date,
    merge_day,
    panel_links,
    pdf_links,
    period_links,
    safe_filename,
    save_pdf,
)


class DigraFetcherTests(unittest.TestCase):
    def test_discovers_sitzungen_period_links(self):
        soup = BeautifulSoup(
            '<a href="/timetable?from=2025">Sitzungen 2025/2026</a>'
            '<a href="/other">Gemeinderatssitzungen</a>',
            "html.parser",
        )
        self.assertEqual(
            period_links(soup, "https://digra.graz.at/timetable"),
            ["https://digra.graz.at/timetable?from=2025"],
        )

    def test_meeting_date_prefers_invitation_date(self):
        soup = BeautifulSoup(
            "Graz, am 30.10.2026 Einladung zu der am Donnerstag, dem "
            "27.08.2026 stattfindenden Sitzung",
            "html.parser",
        )
        self.assertEqual(meeting_date(soup), "20260827")

    def test_meeting_date_uses_timetable_context_as_fallback(self):
        soup = BeautifulSoup("Einladung", "html.parser")
        self.assertEqual(meeting_date(soup, "27.08.2026 Sitzung"), "20260827")

    def test_document_links_exclude_global_documents_navigation(self):
        soup = BeautifulSoup(
            '<a href="/documents?init=true">Materialien</a>'
            '<a href="/document?ref=entry">Einlagezahl 4/1</a>',
            "html.parser",
        )
        self.assertEqual(
            panel_links(soup, "https://digra.graz.at/meeting?ref=meeting"),
            [("https://digra.graz.at/document?ref=entry", "Einlagezahl 4/1")],
        )

    def test_safe_filename_is_ascii_and_stable(self):
        self.assertEqual(
            safe_filename("Einladung Gemeinderatssitzung.pdf", "https://example.test/a"),
            "einladung_gemeinderatssitzung",
        )

    def test_pdf_links_keep_only_invitation_and_minutes_from_anlagen(self):
        soup = BeautifulSoup(
            '<div class="menu"><div class="menu-title">Anlagen</div>'
            '<a href="/pdf?ref=1" title="Anlage Antrag.pdf">Download</a>'
            '<a href="/pdf?ref=2" title="Einladung zur Sitzung.pdf">Download</a>'
            '<a href="/Protokoll.pdf">Download</a>'
            "</div>"
            '<a href="/Anlage_ausserhalb.pdf">Anlage ausserhalb.pdf</a>',
            "html.parser",
        )

        self.assertEqual(
            pdf_links(soup, "https://digra.graz.at/meeting"),
            [
                DownloadLink(
                    "https://digra.graz.at/pdf?ref=2", "Einladung zur Sitzung.pdf"
                ),
                DownloadLink("https://digra.graz.at/Protokoll.pdf", "Download"),
                DownloadLink(
                    "https://digra.graz.at/Anlage_ausserhalb.pdf",
                    "Anlage ausserhalb.pdf",
                ),
            ],
        )

    def test_save_pdf_skips_alternate_signed_edition_before_download(self):
        editions = (
            ("Sitzungsprotokoll_signiert.pdf", "20260827_sitzungsprotokoll.pdf"),
            ("Sitzungsprotokoll.pdf", "20260827_sitzungsprotokoll_signiert.pdf"),
        )
        for link_name, downloaded_name in editions:
            with self.subTest(link_name=link_name):
                session = Mock()
                result = save_pdf(
                    session,
                    DownloadLink("https://example.test/document.pdf", link_name),
                    "20260827",
                    Path("unused"),
                    {downloaded_name},
                )

                self.assertIsNone(result)
                session.get.assert_not_called()

    def test_merge_writes_one_pdf_without_modifying_sources(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            source_paths = []
            for name, text in (("one.pdf", "Invitation"), ("two.pdf", "Agenda")):
                path = folder / name
                with pymupdf.open() as pdf:
                    pdf.new_page().insert_text((72, 72), text)
                    pdf.save(path)
                source_paths.append(path)
            output = folder / "20260827.pdf"

            merge_day(source_paths, output)

            with pymupdf.open(output) as merged:
                self.assertEqual(merged.page_count, 2)
                self.assertIn("Invitation", merged[0].get_text())
                self.assertIn("Agenda", merged[1].get_text())
            self.assertTrue(all(path.exists() for path in source_paths))


if __name__ == "__main__":
    unittest.main()