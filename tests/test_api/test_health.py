import unittest
from fastapi.testclient import TestClient
from api.main import app

class TestHealthApi(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_root_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "CricGPT API")

    def test_v1_health(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "CricGPT API")

    def test_v1_health_ready(self):
        response = self.client.get("/api/v1/health/ready")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ready")
        self.assertEqual(data["database"], "connected")
