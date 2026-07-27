import unittest
from fastapi.testclient import TestClient
from api.main import app

class TestVenuesApi(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_get_venue_summary_exact(self):
        response = self.client.get("/api/v1/venues/Wankhede Stadium/summary")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["data"]["venue_name"], "Wankhede Stadium")
        self.assertGreater(json_data["data"]["matches_played"], 0)

    def test_get_venue_summary_alias(self):
        # Feroz Shah Kotla should normalize to Arun Jaitley Stadium
        response = self.client.get("/api/v1/venues/Feroz Shah Kotla/summary")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["data"]["venue_name"], "Arun Jaitley Stadium")

    def test_get_venue_summary_invalid(self):
        response = self.client.get("/api/v1/venues/NonExistentVenueXYZ/summary")
        self.assertEqual(response.status_code, 404)
        json_data = response.json()
        self.assertFalse(json_data["success"])
        self.assertEqual(json_data["error"]["type"], "VenueNotFoundError")
