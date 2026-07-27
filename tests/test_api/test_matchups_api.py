import unittest
from fastapi.testclient import TestClient
from api.main import app

class TestMatchupsApi(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_kohli_vs_bumrah(self):
        response = self.client.get("/api/v1/matchups/batter-vs-bowler?batter=Virat Kohli&bowler=Jasprit Bumrah")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["data"]["batter_name"], "V Kohli")
        self.assertEqual(json_data["data"]["bowler_name"], "JJ Bumrah")
        self.assertIn("strike_rate", json_data["data"])

    def test_gayle_vs_malinga(self):
        # Chris Gayle -> CH Gayle, Lasith Malinga -> SL Malinga
        response = self.client.get("/api/v1/matchups/batter-vs-bowler?batter=Chris Gayle&bowler=Lasith Malinga")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["data"]["batter_name"], "CH Gayle")
        self.assertEqual(json_data["data"]["bowler_name"], "SL Malinga")
