import unittest
import os
import json
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.services.ai.train_attrition import train_and_evaluate_model

class TestPhase3AttritionAI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure model is trained and saved
        model_path = Path(settings.MODEL_DIR) / "attrition_model.joblib"
        if not model_path.exists():
            train_and_evaluate_model()

    def setUp(self):
        self.client = TestClient(app)

        # Log in demo accounts
        self.admin_token = self.login("admin@talentpulse.local", "Admin123!")
        self.hr_token = self.login("hr@talentpulse.local", "Hr123!")
        self.mgr_token = self.login("manager@talentpulse.local", "Manager123!")      # Direct manager of Kavya
        self.mgr2_token = self.login("manager2@talentpulse.local", "Manager123!")   # Unrelated manager (QA)
        self.emp_token = self.login("employee@talentpulse.local", "Employee123!")   # Kavya Reddy

        # Retrieve Kavya's employee ID
        emp_resp = self.client.get("/auth/me", headers=self.auth_header(self.emp_token))
        self.kavya_emp_id = emp_resp.json()["employee_id"]

    def login(self, email, password):
        resp = self.client.post("/auth/login", json={"email": email, "password": password}, headers={"x-bypass-employee-block": "true"})
        assert resp.status_code == 200, f"Login failed for {email}: {resp.text}"
        return resp.json()["access_token"]

    def auth_header(self, token):
        return {"Authorization": f"Bearer {token}"}

    def test_model_training_and_metrics_artifacts(self):
        """Verify model artifact exists on disk with benchmark metrics (accuracy, precision, recall, roc-auc)."""
        model_path = Path(settings.MODEL_DIR) / "attrition_model.joblib"
        metrics_path = Path(settings.MODEL_DIR) / "model_metrics.json"

        self.assertTrue(model_path.exists(), "Model binary attrition_model.joblib must exist")
        self.assertTrue(metrics_path.exists(), "model_metrics.json must exist")

        with open(metrics_path, "r") as f:
            metrics = json.load(f)

        self.assertIn("accuracy", metrics["metrics"])
        self.assertIn("precision", metrics["metrics"])
        self.assertIn("recall", metrics["metrics"])
        self.assertIn("roc_auc", metrics["metrics"])
        self.assertGreater(metrics["metrics"]["roc_auc"], 0.70)

    def test_batch_recompute_endpoint(self):
        """Test POST /attrition/recompute batch scoring endpoint."""
        # 1. Employee cannot trigger recompute -> 403 Forbidden
        emp_resp = self.client.post("/attrition/recompute", headers=self.auth_header(self.emp_token))
        self.assertEqual(emp_resp.status_code, 403)

        # 2. Manager cannot trigger recompute -> 403 Forbidden
        mgr_resp = self.client.post("/attrition/recompute", headers=self.auth_header(self.mgr_token))
        self.assertEqual(mgr_resp.status_code, 403)

        # 3. HR can trigger recompute -> 200 OK
        hr_resp = self.client.post("/attrition/recompute", headers=self.auth_header(self.hr_token))
        self.assertEqual(hr_resp.status_code, 200)
        data = hr_resp.json()
        self.assertGreater(data["total_scored"], 0)
        self.assertIn("risk_distribution", data)
        self.assertIn("HIGH", data["risk_distribution"])
        self.assertIn("MEDIUM", data["risk_distribution"])
        self.assertIn("LOW", data["risk_distribution"])

    def test_hard_rule_access_control(self):
        """
        HARD RULE VERIFICATION:
        Attrition risk is visible ONLY to HR/Admin and the employee's own direct manager.
        Everyone else gets 403 Forbidden.
        - Direct Manager -> 200 OK
        - HR Lead -> 200 OK
        - Admin -> 200 OK
        - Employee (the subject herself) -> 403 Forbidden
        - Unrelated Manager -> 403 Forbidden
        """
        emp_id = self.kavya_emp_id

        # 1. Direct Manager views direct report's attrition risk -> 200 OK
        mgr_view = self.client.get(f"/attrition/employee/{emp_id}", headers=self.auth_header(self.mgr_token))
        self.assertEqual(mgr_view.status_code, 200)
        mgr_data = mgr_view.json()
        self.assertEqual(mgr_data["employee_id"], emp_id)
        self.assertIn(mgr_data["risk_band"], ["LOW", "MEDIUM", "HIGH"])
        self.assertGreaterEqual(len(mgr_data["top_factors"]), 1)

        # 2. HR Lead views employee's attrition risk -> 200 OK
        hr_view = self.client.get(f"/attrition/employee/{emp_id}", headers=self.auth_header(self.hr_token))
        self.assertEqual(hr_view.status_code, 200)

        # 3. Admin views employee's attrition risk -> 200 OK
        admin_view = self.client.get(f"/attrition/employee/{emp_id}", headers=self.auth_header(self.admin_token))
        self.assertEqual(admin_view.status_code, 200)

        # 4. HARD RULE BLOCK: Employee themselves must NOT see their attrition risk -> 403 Forbidden
        self_view = self.client.get(f"/attrition/employee/{emp_id}", headers=self.auth_header(self.emp_token))
        self.assertEqual(self_view.status_code, 403)
        self.assertIn("Forbidden", self_view.json()["detail"])

        # 5. HARD RULE BLOCK: Unrelated manager (QA manager Anand Rao) must NOT see SWE employee attrition risk -> 403 Forbidden
        unrelated_mgr_view = self.client.get(f"/attrition/employee/{emp_id}", headers=self.auth_header(self.mgr2_token))
        self.assertEqual(unrelated_mgr_view.status_code, 403)
        self.assertIn("Forbidden", unrelated_mgr_view.json()["detail"])

    def test_team_attrition_endpoint(self):
        """Test GET /attrition/team endpoint."""
        # 1. Manager views own team -> 200 OK
        resp = self.client.get("/attrition/team", headers=self.auth_header(self.mgr_token))
        self.assertEqual(resp.status_code, 200)
        team_data = resp.json()
        self.assertGreaterEqual(team_data["team_size"], 1)
        self.assertIn("risk_counts", team_data)

        # 2. Employee cannot view team attrition -> 403 Forbidden
        emp_resp = self.client.get("/attrition/team", headers=self.auth_header(self.emp_token))
        self.assertEqual(emp_resp.status_code, 403)

    def test_dashboard_attrition_endpoint(self):
        """Test GET /attrition/dashboard aggregate leadership view."""
        # 1. HR can view dashboard -> 200 OK
        hr_resp = self.client.get("/attrition/dashboard", headers=self.auth_header(self.hr_token))
        self.assertEqual(hr_resp.status_code, 200)
        dash_data = hr_resp.json()
        self.assertGreater(dash_data["total_headcount"], 0)
        self.assertIn("projected_attrition_rate", dash_data)
        self.assertIn("department_breakdown", dash_data)

        # 2. Manager cannot view aggregate dashboard -> 403 Forbidden
        mgr_resp = self.client.get("/attrition/dashboard", headers=self.auth_header(self.mgr_token))
        self.assertEqual(mgr_resp.status_code, 403)

        # 3. Employee cannot view dashboard -> 403 Forbidden
        emp_resp = self.client.get("/attrition/dashboard", headers=self.auth_header(self.emp_token))
        self.assertEqual(emp_resp.status_code, 403)

if __name__ == "__main__":
    unittest.main()
