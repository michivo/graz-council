import sqlite3
import tempfile
import unittest
from pathlib import Path

import main


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
                        "2026-01-01",
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


if __name__ == "__main__":
    unittest.main()
