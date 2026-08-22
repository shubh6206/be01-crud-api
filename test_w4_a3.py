import os
import sys
import unittest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from main import app, db

class TestTaskAPIPostgreSQL(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.client.post("/reset")

    def test_root_and_health(self):
        res_root = self.client.get("/")
        self.assertEqual(res_root.status_code, 200)
        data = res_root.json()
        self.assertEqual(data["name"], "Task API")
        self.assertEqual(data["version"], "3.0")
        self.assertIn("/tasks", data["endpoints"])

        res_health = self.client.get("/health")
        self.assertEqual(res_health.status_code, 200)
        self.assertEqual(res_health.json(), {"status": "ok", "db": "ok"})

    def test_get_tasks_seeded(self):
        res = self.client.get("/tasks")
        self.assertEqual(res.status_code, 200)
        tasks = res.json()
        self.assertEqual(len(tasks), 3)
        self.assertEqual(tasks[0]["id"], 1)
        self.assertEqual(tasks[0]["title"], "Buy groceries")
        self.assertFalse(tasks[0]["done"])
        self.assertTrue(tasks[2]["done"])

    def test_get_task_by_id(self):
        res = self.client.get("/tasks/1")
        self.assertEqual(res.status_code, 200)
        task = res.json()
        self.assertEqual(task["id"], 1)
        self.assertEqual(task["title"], "Buy groceries")

        # Non-existent ID (404)
        res404 = self.client.get("/tasks/999")
        self.assertEqual(res404.status_code, 404)
        self.assertEqual(res404.json(), {"error": "Task 999 not found"})

    def test_create_task_validation_and_sanitization(self):
        # Valid creation
        res = self.client.post("/tasks", json={"title": "Deploy to production"})
        self.assertEqual(res.status_code, 201)
        task = res.json()
        self.assertEqual(task["id"], 4)
        self.assertEqual(task["title"], "Deploy to production")
        self.assertFalse(task["done"])

        # Title whitespace sanitization
        res_ws_clean = self.client.post("/tasks", json={"title": "  Task with spaces  "})
        self.assertEqual(res_ws_clean.status_code, 201)
        self.assertEqual(res_ws_clean.json()["title"], "Task with spaces")

        # Validation: empty body -> 400 Bad Request
        res_empty = self.client.post("/tasks", json={})
        self.assertEqual(res_empty.status_code, 400)
        self.assertEqual(res_empty.json(), {"error": "Title is required and cannot be empty"})

        # Validation: whitespace only -> 400 Bad Request
        res_ws = self.client.post("/tasks", json={"title": "   "})
        self.assertEqual(res_ws.status_code, 400)
        self.assertEqual(res_ws.json(), {"error": "Title is required and cannot be empty"})

    def test_update_task(self):
        # Valid update
        res = self.client.put("/tasks/1", json={"title": "Buy organic groceries", "done": True})
        self.assertEqual(res.status_code, 200)
        task = res.json()
        self.assertEqual(task["id"], 1)
        self.assertEqual(task["title"], "Buy organic groceries")
        self.assertTrue(task["done"])

        # 404 for unknown ID
        res404 = self.client.put("/tasks/999", json={"title": "test"})
        self.assertEqual(res404.status_code, 404)
        self.assertEqual(res404.json(), {"error": "Task 999 not found"})

        # 400 for empty title
        res400 = self.client.put("/tasks/1", json={"title": ""})
        self.assertEqual(res400.status_code, 400)
        self.assertEqual(res400.json(), {"error": "Title cannot be empty"})

    