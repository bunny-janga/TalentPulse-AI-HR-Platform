import unittest
from fastapi.testclient import TestClient
from app.main import app

class TestPhase6AdminMetrics(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

        # Log in demo accounts
        self.admin_token = self.login("admin@talentpulse.local", "Admin123!")
        self.hr_token = self.login("hr@talentpulse.local", "Hr123!")
        self.mgr_token = self.login("manager@talentpulse.local", "Manager123!")
        self.emp_token = self.login("employee@talentpulse.local", "Employee123!")

    def login(self, email, password):
        resp = self.client.post("/auth/login", json={"email": email, "password": password}, headers={"x-bypass-employee-block": "true"})
        assert resp.status_code == 200, f"Login failed for {email}: {resp.text}"
        return resp.json()["access_token"]

    def auth_header(self, token):
        return {"Authorization": f"Bearer {token}"}

    def test_admin_metrics_access_authorized(self):
        """Admin and HR can access comprehensive workforce metrics."""
        # 1. Admin call
        resp = self.client.get("/admin/metrics", headers=self.auth_header(self.admin_token))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertGreater(data["total_headcount"], 0)
        self.assertGreaterEqual(len(data["department_headcounts"]), 6)
        self.assertIn("attrition_summary", data)
        self.assertIn("leave_trends", data)
        self.assertIn("review_metrics", data)

        # 2. HR call
        hr_resp = self.client.get("/admin/metrics", headers=self.auth_header(self.hr_token))
        self.assertEqual(hr_resp.status_code, 200)

    def test_admin_metrics_role_restriction(self):
        """Managers and Employees are strictly forbidden from viewing company-wide admin metrics."""
        # 1. Manager -> 403
        mgr_resp = self.client.get("/admin/metrics", headers=self.auth_header(self.mgr_token))
        self.assertEqual(mgr_resp.status_code, 403)
        self.assertIn("Forbidden", mgr_resp.json()["detail"])

        # 2. Employee -> 403
        emp_resp = self.client.get("/admin/metrics", headers=self.auth_header(self.emp_token))
        self.assertEqual(emp_resp.status_code, 403)

        # 3. Unauthenticated -> 401
        anon_resp = self.client.get("/admin/metrics")
        self.assertEqual(anon_resp.status_code, 401)

if __name__ == "__main__":
    unittest.main()
