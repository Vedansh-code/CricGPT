import unittest
from fastapi.testclient import TestClient
from api.main import app

class TestBowlingApi(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_top_wicket_takers(self):
        response = self.client.get("/api/v1/bowling/top-wicket-takers?limit=5")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(len(json_data["data"]), 5)
        self.assertEqual(json_data["meta"]["limit"], 5)
        self.assertIn("economy_rate", json_data["data"][0])

    def test_best_figures(self):
        response = self.client.get("/api/v1/bowling/best-figures?limit=3")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(len(json_data["data"]), 3)
        self.assertIn("wickets", json_data["data"][0])

    def test_player_economy(self):
        response = self.client.get("/api/v1/bowling/Jasprit Bumrah/economy")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["data"]["player_name"], "JJ Bumrah")
        self.assertIn("economy_rate", json_data["data"])
