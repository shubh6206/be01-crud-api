import os
import sys
import unittest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from main import app

class TestAuthAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_root_and_public_info(self):
        # Root endpoint
        res_root = self.client.get("/")
        self.assertEqual(res_root.status_code, 200)
        data = res_root.json()
        self.assertEqual(data["name"], "Auth API")
        self.assertEqual(data["auth_provider"], "Supabase Auth")

        # Public info endpoint (no auth)
        res_pub = self.client.get("/public/info")
        self.assertEqual(res_pub.status_code, 200)
        self.assertEqual(res_pub.json(), {"message": "Welcome stranger! This info is public."})

    def test_signup_and_validation(self):
        # Missing payload
        res_empty = self.client.post("/auth/signup", json={})
        self.assertEqual(res_empty.status_code, 400)
        self.assertEqual(res_empty.json(), {"error": "Email and password are required"})

        # Empty whitespace fields
        res_ws = self.client.post("/auth/signup", json={"email": "   ", "password": ""})
        self.assertEqual(res_ws.status_code, 400)
        self.assertEqual(res_ws.json(), {"error": "Email and password are required"})

        # Successful signup
        res_valid = self.client.post("/auth/signup", json={"email": "test@example.com", "password": "password123"})
        self.assertEqual(res_valid.status_code, 201)
        self.assertIn("user", res_valid.json())

    def test_login_and_validation(self):
        # Invalid credentials
        res_bad = self.client.post("/auth/login", json={"email": "invalid@example.com", "password": "wrongpassword"})
        self.assertEqual(res_bad.status_code, 401)
        self.assertEqual(res_bad.json(), {"error": "Invalid login credentials"})

        # Successful login
        res_valid = self.client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})
        self.assertEqual(res_valid.status_code, 200)
        data = res_valid.json()
        self.assertIn("access_token", data)
        self.assertIn("refresh_token", data)
        self.assertEqual(data["token_type"], "bearer")

    def test_protected_routes_and_token_verification(self):
        # Missing token -> 401
        res_no_auth = self.client.get("/protected/profile")
        self.assertEqual(res_no_auth.status_code, 401)
        self.assertEqual(res_no_auth.json(), {"error": "Access token required"})

        # Invalid/tampered token -> 401
        res_bad_token = self.client.get(
            "/protected/profile",
            headers={"Authorization": "Bearer invalid_tampered_token_xyz"}
        )
        self.assertEqual(res_bad_token.status_code, 401)
        self.assertEqual(res_bad_token.json(), {"error": "Invalid or expired token"})

        # Valid login -> token -> protected profile
        login_res = self.client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})
        token = login_res.json()["access_token"]

        res_prof = self.client.get(
            "/protected/profile",
            headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(res_prof.status_code, 200)
        self.assertEqual(res_prof.json()["email"], "test@example.com")

        # Protected dashboard route using same dependency
        res_dash = self.client.get(
            "/protected/dashboard",
            headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(res_dash.status_code, 200)
        self.assertIn("user", res_dash.json())

    def test_logout_route(self):
        login_res = self.client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})
        token = login_res.json()["access_token"]

        res_logout = self.client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(res_logout.status_code, 204)

if __name__ == "__main__":
    unittest.main(verbosity=2)
