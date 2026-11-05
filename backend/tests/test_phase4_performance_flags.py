import unittest
from fastapi.testclient import TestClient
from app.main import app

class TestPhase4PerformanceFlags(unittest.TestCase):
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

    def test_performance_flags_detection(self):
        """Test detection of 2+ consecutive declining performance reviews by HR/Admin."""
        resp = self.client.get("/ai/performance-flags", headers=self.auth_header(self.hr_token))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreater(data["total_flagged"], 0)
        self.assertGreater(data["critical_count"] + data["warning_count"], 0)

        # Verify attributes on each flagged employee
        for item in data["flagged_employees"]:
            self.assertGreaterEqual(item["consecutive_declines"], 2)
            self.assertIn(item["severity"], ["WARNING", "CRITICAL"])
            self.assertTrue(len(item["action_recommendation"]) > 10)
            self.assertGreaterEqual(len(item["previous_ratings"]), 3)

            # Check that the ratings are strictly declining at the tail
            ratings = [r["rating"] for r in item["previous_ratings"]]
            self.assertGreater(ratings[-2], ratings[-1])
            self.assertGreater(ratings[-3], ratings[-2])

    def test_performance_flags_severity_filter(self):
        """Test filtering performance flags by severity (CRITICAL vs WARNING)."""
        crit_resp = self.client.get("/ai/performance-flags?severity=CRITICAL", headers=self.auth_header(self.hr_token))
        self.assertEqual(crit_resp.status_code, 200)
        crit_data = crit_resp.json()
        for item in crit_data["flagged_employees"]:
            self.assertEqual(item["severity"], "CRITICAL")

    def test_performance_flags_access_control(self):
        """Test role-based access control for /ai/performance-flags."""
        # 1. Employee cannot view performance flags -> 403 Forbidden
        emp_resp = self.client.get("/ai/performance-flags", headers=self.auth_header(self.emp_token))
        self.assertEqual(emp_resp.status_code, 403)
        self.assertIn("Forbidden", emp_resp.json()["detail"])

        # 2. Manager can access their direct reports' flags -> 200 OK
        mgr_resp = self.client.get("/ai/performance-flags", headers=self.auth_header(self.mgr_token))
        self.assertEqual(mgr_resp.status_code, 200)

        # 3. Admin has access across the organization -> 200 OK
        admin_resp = self.client.get("/ai/performance-flags", headers=self.auth_header(self.admin_token))
        self.assertEqual(admin_resp.status_code, 200)

    def test_trend_fed_into_attrition_features(self):
        """Verify that declining performance trend feeds directly into employee attrition features and top factors."""
        # Find one of the flagged employees from /ai/performance-flags
        flags_resp = self.client.get("/ai/performance-flags", headers=self.auth_header(self.hr_token))
        flagged_list = flags_resp.json()["flagged_employees"]
        self.assertGreater(len(flagged_list), 0)

        flagged_emp_id = flagged_list[0]["employee_id"]

        # Retrieve their attrition profile as HR
        attr_resp = self.client.get(f"/attrition/employee/{flagged_emp_id}", headers=self.auth_header(self.hr_token))
        self.assertEqual(attr_resp.status_code, 200)
        attr_data = attr_resp.json()

        # Check that performance decline is acknowledged in features or factors
        features = attr_data.get("features", {})
        self.assertTrue(features.get("has_consecutive_decline", False))
        self.assertLessEqual(features.get("performance_trend", 0.0), 0.0)

        factors = attr_data.get("top_factors", [])
        has_perf_factor = any("Performance" in f or "declining" in f.lower() for f in factors)
        self.assertTrue(has_perf_factor, f"Expected performance decline in top factors: {factors}")

if __name__ == "__main__":
    unittest.main()
