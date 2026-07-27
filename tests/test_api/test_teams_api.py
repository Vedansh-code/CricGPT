import unittest
from fastapi.testclient import TestClient
from api.main import app

class TestTeamsApi(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_team_record(self):
        response = self.client.get("/api/v1/teams/RCB/record")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["data"]["team_name"], "Royal Challengers Bangalore")
        self.assertIn("win_percentage", json_data["data"])

    def test_head_to_head(self):
        response = self.client.get("/api/v1/teams/head-to-head?team1=MI&team2=CSK")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["data"]["team1"], "Mumbai Indians")
        self.assertEqual(json_data["data"]["team2"], "Chennai Super Kings")
        self.assertGreater(json_data["data"]["matches_played"], 0)
        self.assertGreater(len(json_data["data"]["recent_matches"]), 0)
