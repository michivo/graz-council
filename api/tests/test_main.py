import datetime
import sqlite3
import tempfile
import unittest
from pathlib import Path

from api.src import main


class ApiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "test.db"
        self.original_db_path = main.DB_PATH
        main.DB_PATH = str(self.database_path)
        main.app.config.update(TESTING=True)
        self.create_database()
        self.client = main.app.test_client()

    def tearDown(self) -> None:
        main.DB_PATH = self.original_db_path
        self.temporary_directory.cleanup()

    def create_database(self) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                CREATE VIRTUAL TABLE fts5_index USING fts5(
                    id,
                    filename,
                    page,
                    text,
                    source_url,
                    document_date,
                    document_title,
                    MATCHED
                )
                """
            )
            connection.executemany(
                """
                INSERT INTO fts5_index (
                    id, filename, page, text, source_url, document_date,
                    document_title, MATCHED
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        index,
                        f"meeting-{index}.pdf",
                        index,
                        "The council approved the budget.",
                        f"https://example.test/meeting-{index}.pdf",
                        (
                            datetime.date(2026, 1, 1) + datetime.timedelta(days=index)
                        ).isoformat(),
                        f"Meeting {index}",
                        "",
                    )
                    for index in range(1, 102)
                ],
            )

    def test_health_returns_ok(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})

    def test_database_health_returns_ok(self) -> None:
        response = self.client.get("/health-db")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})

    def test_search_requires_a_query(self) -> None:
        response = self.client.get("/search")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {"error": "Missing query parameter 'q'"})

    def test_search_returns_matching_documents(self) -> None:
        response = self.client.get("/search?q=budget&limit=2&offset=1")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["query"], "budget")
        self.assertEqual(payload["count"], 2)
        self.assertEqual(
            set(payload["results"][0]),
            {
                "filename",
                "page",
                "source_url",
                "document_date",
                "document_title",
                "snippet",
            },
        )

    def test_search_caps_negative_and_oversized_limits(self) -> None:
        response = self.client.get("/search?q=budget&limit=-1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["count"], 1)

        response = self.client.get("/search?q=budget&limit=1000")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["count"], 100)

    def test_search_sorts_by_date_ascending(self) -> None:
        response = self.client.get("/search?q=budget&sort=date_asc&limit=5")

        self.assertEqual(response.status_code, 200)
        dates = [r["document_date"] for r in response.get_json()["results"]]
        self.assertEqual(dates, sorted(dates))
        self.assertEqual(dates[0], "2026-01-02")

    def test_search_sorts_by_date_descending(self) -> None:
        response = self.client.get("/search?q=budget&sort=date_desc&limit=5")

        self.assertEqual(response.status_code, 200)
        dates = [r["document_date"] for r in response.get_json()["results"]]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_search_rejects_invalid_sort_value(self) -> None:
        response = self.client.get("/search?q=budget&sort=bogus")

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_search_filters_by_date_range(self) -> None:
        response = self.client.get(
            "/search?q=budget&date_from=2026-01-10&date_to=2026-01-12&limit=100"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["count"], 3)
        dates = {r["document_date"] for r in payload["results"]}
        self.assertEqual(dates, {"2026-01-10", "2026-01-11", "2026-01-12"})

    def test_search_filters_by_date_from_only(self) -> None:
        response = self.client.get(
            "/search?q=budget&date_from=2026-04-10&limit=100"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["count"] > 0)
        self.assertTrue(all(r["document_date"] >= "2026-04-10" for r in payload["results"]))

    def test_search_rejects_invalid_date_format(self) -> None:
        response = self.client.get("/search?q=budget&date_from=not-a-date")

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())


if __name__ == "__main__":
    unittest.main()
