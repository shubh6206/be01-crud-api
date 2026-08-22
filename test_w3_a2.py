import os
import sys
import unittest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from main import app, init_db, db

class TestTaskAPISQLite(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.client.post("/reset")

    def test_root_and_health(self):
        res_root = self.client.get("/")
        self.assertEqual(res_root.status_code, 200)
        data = res_root.json()
        self.assertEqual(data["name"], "Task API")
        self.assertEqual(data["storage"], "SQLite (tasks.db)")
        self.assertIn("/tasks", data["endpoints"])

        res_health = self.client.get("/health")
        self.assertEqual(res_health.status_code, 200)
        self.assertEqual(res_health.json(), {"status": "ok"})

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

        # Non-existent ID
        res404 = self.client.get("/tasks/999")
        self.assertEqual(res404.status_code, 404)
        self.assertIn("error", res404.json())

    def test_create_task_and_validation(self):
        # Valid creation
        res = self.client.post("/tasks", json={"title": "Write documentation"})
        self.assertEqual(res.status_code, 201)
        task = res.json()
        self.assertEqual(task["id"], 4)
        self.assertEqual(task["title"], "Write documentation")
        self.assertFalse(task["done"])

        # Validation: empty body
        res_empty = self.client.post("/tasks", json={})
        self.assertEqual(res_empty.status_code, 400)
        self.assertIn("error", res_empty.json())

        # Validation: whitespace title
        res_ws = self.client.post("/tasks", json={"title": "   "})
        self.assertEqual(res_ws.status_code, 400)
        self.assertIn("error", res_ws.json())

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

        # 400 for empty title
        res400 = self.client.put("/tasks/1", json={"title": ""})
        self.assertEqual(res400.status_code, 400)

    def test_delete_task(self):
        res = self.client.delete("/tasks/1")
        self.assertEqual(res.status_code, 204)
        self.assertEqual(res.text, "")

        # Verify gone
        res_get = self.client.get("/tasks/1")
        self.assertEqual(res_get.status_code, 404)

        # 404 on deleting already deleted
        res_del_again = self.client.delete("/tasks/1")
        self.assertEqual(res_del_again.status_code, 404)

    def test_extras_filtering_and_stats(self):
        # Done filter
        res_done = self.client.get("/tasks?done=true")
        self.assertEqual(res_done.status_code, 200)
        self.assertEqual(len(res_done.json()), 1)
        self.assertEqual(res_done.json()[0]["id"], 3)

        # Search filter
        res_search = self.client.get("/tasks?search=FastAPI")
        self.assertEqual(res_search.status_code, 200)
        self.assertEqual(len(res_search.json()), 1)
        self.assertEqual(res_search.json()[0]["title"], "Read FastAPI documentation")

        # Sorting
        res_sort = self.client.get("/tasks?sort=title")
        self.assertEqual(res_sort.status_code, 200)
        titles = [t["title"] for t in res_sort.json()]
        self.assertEqual(titles, sorted(titles, key=str.lower))

        # Stats
        res_stats = self.client.get("/stats")
        self.assertEqual(res_stats.status_code, 200)
        stats = res_stats.json()
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["done"], 1)
        self.assertEqual(stats["open"], 2)

    def test_persistence_across_instances(self):
        # Create task
        res_create = self.client.post("/tasks", json={"title": "Persistent task"})
        task_id = res_create.json()["id"]

        # Re-initialize DB object simulating server restart
        init_db()
        res_get = self.client.get(f"/tasks/{task_id}")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["title"], "Persistent task")

if __name__ == "__main__":
    unittest.main(verbosity=2)
