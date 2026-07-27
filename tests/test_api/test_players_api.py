import unittest
from fastapi.testclient import TestClient
from api.main import app

class TestPlayersApi(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_search_players(self):
        response = self.client.get("/api/v1/players/search?q=Kohli")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertGreater(len(json_data["data"]), 0)
        self.assertIn("player_name", json_data["data"][0])
        self.assertEqual(json_data["meta"]["count"], len(json_data["data"]))

    def test_get_player_profile(self):
        response = self.client.get("/api/v1/players/Virat Kohli/profile")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["data"]["player_name"], "V Kohli")

    def test_get_player_career(self):
        response = self.client.get("/api/v1/players/Virat Kohli/career")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["data"]["player_name"], "V Kohli")
        self.assertGreater(json_data["data"]["matches"], 0)

    def test_get_player_recent_matches(self):
        response = self.client.get("/api/v1/players/Virat Kohli/recent-matches?limit=3")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(len(json_data["data"]), 3)
        self.assertEqual(json_data["meta"]["limit"], 3)

    def test_get_player_matches(self):
        response = self.client.get("/api/v1/players/Virat Kohli/matches")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertGreater(len(json_data["data"]), 0)
