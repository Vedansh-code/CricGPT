import unittest
from fastapi.testclient import TestClient
from api.main import app

class TestBattingApi(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_top_run_scorers(self):
        response = self.client.get("/api/v1/batting/top-run-scorers?limit=5")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(len(json_data["data"]), 5)
        self.assertEqual(json_data["meta"]["limit"], 5)
        self.assertIn("average", json_data["data"][0])

    def test_highest_scores(self):
        response = self.client.get("/api/v1/batting/highest-scores?limit=3")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(len(json_data["data"]), 3)
        self.assertIn("runs", json_data["data"][0])

    def test_player_average(self):
        response = self.client.get("/api/v1/batting/Virat Kohli/average")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["data"]["player_name"], "V Kohli")
        self.assertIn("batting_average", json_data["data"])

    def test_player_strike_rate(self):
        response = self.client.get("/api/v1/batting/Virat Kohli/strike-rate")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["data"]["player_name"], "V Kohli")
        self.assertIn("strike_rate", json_data["data"])

    def test_player_boundary_percentage(self):
        response = self.client.get("/api/v1/batting/Virat Kohli/boundary-percentage")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["data"]["player_name"], "V Kohli")
        self.assertIn("boundary_runs_percentage", json_data["data"])
