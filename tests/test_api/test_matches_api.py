import unittest
from fastapi.testclient import TestClient
from api.main import app
from analytics.database import get_connection

class TestMatchesApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT match_id FROM matches LIMIT 1")
            cls.match_id = cursor.fetchone()[0]
        finally:
            conn.close()

    def setUp(self):
        self.client = TestClient(app)

    def test_get_match_summary(self):
        response = self.client.get(f"/api/v1/matches/{self.match_id}/summary")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["data"]["match_id"], self.match_id)
        self.assertIn("venue", json_data["data"])
        self.assertIn("team1", json_data["data"])
        self.assertIn("team2", json_data["data"])

    def test_get_match_scorecard(self):
        response = self.client.get(f"/api/v1/matches/{self.match_id}/scorecard")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["data"]["match_id"], self.match_id)
        self.assertGreater(len(json_data["data"]["innings"]), 0)

    def test_get_match_invalid(self):
        response = self.client.get("/api/v1/matches/99999999/summary")
        self.assertEqual(response.status_code, 404)
        json_data = response.json()
        self.assertFalse(json_data["success"])
        self.assertEqual(json_data["error"]["type"], "MatchNotFoundError")
