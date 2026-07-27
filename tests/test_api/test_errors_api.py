import unittest
from fastapi.testclient import TestClient
from api.main import app

class TestErrorsApi(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_player_not_found(self):
        response = self.client.get("/api/v1/players/NonExistentPlayerXYZ/profile")
        self.assertEqual(response.status_code, 404)
        json_data = response.json()
        self.assertFalse(json_data["success"])
        self.assertEqual(json_data["error"]["type"], "PlayerNotFoundError")
        self.assertIn("not found", json_data["error"]["message"])

    def test_team_not_found(self):
        response = self.client.get("/api/v1/teams/NonExistentTeamXYZ/record")
        self.assertEqual(response.status_code, 404)
        json_data = response.json()
        self.assertFalse(json_data["success"])
        self.assertEqual(json_data["error"]["type"], "TeamNotFoundError")

    def test_ambiguity_handler(self):
        # Searching career for "Kohli" should trigger AmbiguousMatchError (V Kohli and T Kohli)
        response = self.client.get("/api/v1/players/Kohli/career")
        self.assertEqual(response.status_code, 409)
        json_data = response.json()
        self.assertFalse(json_data["success"])
        self.assertEqual(json_data["error"]["type"], "AmbiguousMatchError")
        self.assertIn("V Kohli", json_data["error"]["message"])
        self.assertIn("T Kohli", json_data["error"]["message"])

    def test_invalid_limit_validation(self):
        # negative limit
        response = self.client.get("/api/v1/batting/top-run-scorers?limit=-5")
        self.assertEqual(response.status_code, 422)
        json_data = response.json()
        self.assertFalse(json_data["success"])
        self.assertEqual(json_data["error"]["type"], "ValidationError")

        # excessive limit (>100)
        response = self.client.get("/api/v1/batting/top-run-scorers?limit=150")
        self.assertEqual(response.status_code, 422)
        json_data = response.json()
        self.assertFalse(json_data["success"])
        self.assertEqual(json_data["error"]["type"], "ValidationError")

        # invalid type limit
        response = self.client.get("/api/v1/batting/top-run-scorers?limit=abc")
        self.assertEqual(response.status_code, 422)
        json_data = response.json()
        self.assertFalse(json_data["success"])
        self.assertEqual(json_data["error"]["type"], "ValidationError")

    def test_empty_search_query_validation(self):
        # empty q parameter
        response = self.client.get("/api/v1/players/search?q=")
        self.assertEqual(response.status_code, 422)
        json_data = response.json()
        self.assertFalse(json_data["success"])
        self.assertEqual(json_data["error"]["type"], "ValidationError")
