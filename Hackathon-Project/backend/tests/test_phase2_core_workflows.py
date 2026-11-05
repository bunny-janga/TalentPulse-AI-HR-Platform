import unittest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from app.main import app

class TestPhase2CoreWorkflows(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

        # Log in demo users
        self.admin_token = self.login("admin@talentpulse.local", "Admin123!")
        self.hr_token = self.login("hr@talentpulse.local", "Hr123!")
        self.mgr_token = self.login("manager@talentpulse.local", "Manager123!")
        self.mgr2_token = self.login("manager2@talentpulse.local", "Manager123!")
        self.emp_token = self.login("employee@talentpulse.local", "Employee123!")

    def login(self, email, password):
        resp = self.client.post("/auth/login", json={"email": email, "password": password}, headers={"x-bypass-employee-block": "true"})
        assert resp.status_code == 200, f"Login failed for {email}: {resp.text}"
        return resp.json()["access_token"]

    def auth_header(self, token):
        return {"Authorization": f"Bearer {token}"}

    def test_departments_and_hierarchy(self):
        """Test listing departments and retrieving organizational hierarchy."""
        # Departments list
        resp = self.client.get("/departments", headers=self.auth_header(self.emp_token))
        self.assertEqual(resp.status_code, 200)
        depts = resp.json()
        self.assertGreaterEqual(len(depts), 6)
        codes = [d["code"] for d in depts]
        self.assertIn("SWE", codes)
        self.assertIn("QA", codes)

        # Org hierarchy tree
        hier_resp = self.client.get("/org/hierarchy", headers=self.auth_header(self.mgr_token))
        self.assertEqual(hier_resp.status_code, 200)
        hier_data = hier_resp.json()
        self.assertIn("hierarchy_trees", hier_data)
        self.assertGreater(hier_data["total_headcount"], 0)

    def test_employees_directory_and_filter(self):
        """Test employee listing, search filter, and individual profile retrieval."""
        resp = self.client.get("/employees", headers=self.auth_header(self.emp_token))
        self.assertEqual(resp.status_code, 200)
        employees = resp.json()
        self.assertGreaterEqual(len(employees), 3)

        # Search filter
        search_resp = self.client.get("/employees?search=Kavya", headers=self.auth_header(self.emp_token))
        self.assertEqual(search_resp.status_code, 200)
        search_data = search_resp.json()
        self.assertTrue(any("Kavya" in e["full_name"] for e in search_data))

        # Single profile
        emp_id = search_data[0]["id"]
        single_resp = self.client.get(f"/employees/{emp_id}", headers=self.auth_header(self.emp_token))
        self.assertEqual(single_resp.status_code, 200)
        self.assertEqual(single_resp.json()["id"], emp_id)

    def test_leave_workflow_end_to_end(self):
        """Test leave application, listing, and approval by direct manager."""
        import random
        # Random far-future window so repeated runs against the same database never overlap an earlier test request.
        st = date.today() + timedelta(days=random.randint(20, 700))
        en = st + timedelta(days=2)

        # 1. Employee applies for leave
        apply_resp = self.client.post(
            "/leave/apply",
            json={
                "leave_type": "Unpaid Leave",
                "start_date": st.isoformat(),
                "end_date": en.isoformat(),
                "days_count": 3,
                "reason": "Family function in Rajahmundry"
            },
            headers=self.auth_header(self.emp_token)
        )
        self.assertEqual(apply_resp.status_code, 201)
        leave_id = apply_resp.json()["id"]
        self.assertEqual(apply_resp.json()["status"], "PENDING")

        # 2. Employee checks own leaves
        my_leaves = self.client.get("/leave/my", headers=self.auth_header(self.emp_token)).json()
        self.assertTrue(any(l["id"] == leave_id for l in my_leaves))

        # 3. Unrelated manager (mgr2) attempts to approve -> 403 Forbidden
        unrelated_approve = self.client.put(
            f"/leave/{leave_id}/approve",
            json={"comment": "Unauthorized approval attempt"},
            headers=self.auth_header(self.mgr2_token)
        )
        self.assertEqual(unrelated_approve.status_code, 403)

        # 4. Direct manager (mgr1) approves -> 200 OK
        valid_approve = self.client.put(
            f"/leave/{leave_id}/approve",
            json={"comment": "Approved, enjoy your leave."},
            headers=self.auth_header(self.mgr_token)
        )
        self.assertEqual(valid_approve.status_code, 200)
        self.assertEqual(valid_approve.json()["status"], "APPROVED")

    def test_performance_review_workflow(self):
        """Test performance review submission and access control."""
        # Find employee Kavya Reddy's ID (reporting to manager Rajesh Varma)
        search_resp = self.client.get("/employees?search=Kavya+Reddy", headers=self.auth_header(self.hr_token))
        emp_id = search_resp.json()[0]["id"]

        # 1. Direct manager creates a performance review
        create_resp = self.client.post(
            "/reviews",
            json={
                "employee_id": emp_id,
                "review_cycle": f"{__import__('random').randint(2040, 2999)}-H{__import__('random').randint(1, 2)}",
                "rating": 5,
                "feedback": "Exceptional contribution to the cloud migration initiative.",
                "strengths": "Fast learner, proactive ownership, solid code reviews.",
                "growth_areas": "Mentoring junior engineers.",
                "goals": "Lead the Q3 microservice refactor."
            },
            headers=self.auth_header(self.mgr_token)
        )
        self.assertEqual(create_resp.status_code, 201)
        rev_id = create_resp.json()["id"]

        # 2. Employee views own reviews -> 200 OK
        emp_view = self.client.get(f"/reviews/employee/{emp_id}", headers=self.auth_header(self.emp_token))
        self.assertEqual(emp_view.status_code, 200)
        self.assertTrue(any(r["id"] == rev_id for r in emp_view.json()))

        # 3. Unrelated manager views reviews -> 403 Forbidden
        unrelated_view = self.client.get(f"/reviews/employee/{emp_id}", headers=self.auth_header(self.mgr2_token))
        self.assertEqual(unrelated_view.status_code, 403)

    def test_policy_document_library(self):
        """Test listing and uploading HR policy documents."""
        # 1. List pre-seeded policies
        policies_resp = self.client.get("/policies", headers=self.auth_header(self.emp_token))
        self.assertEqual(policies_resp.status_code, 200)
        policies = policies_resp.json()
        self.assertGreaterEqual(len(policies), 3)

        # 2. Employee cannot upload policy -> 403 Forbidden
        emp_upload = self.client.post(
            "/policies/upload",
            data={"title": "Test Policy", "category": "Test", "raw_text": "Sample policy text."},
            headers=self.auth_header(self.emp_token)
        )
        self.assertEqual(emp_upload.status_code, 403)

        # 3. HR uploads policy -> 201 Created
        hr_upload = self.client.post(
            "/policies/upload",
            data={
                "title": "IT Equipment & Asset Care Policy",
                "category": "IT Operations",
                "raw_text": "All employees in the Visakhapatnam center must secure laptops with BitLocker encryption and report any hardware faults within 24 hours to IT desk."
            },
            headers=self.auth_header(self.hr_token)
        )
        self.assertEqual(hr_upload.status_code, 201)
        self.assertEqual(hr_upload.json()["title"], "IT Equipment & Asset Care Policy")

    def test_surveys_and_onboarding(self):
        """Test survey retrieval, results calculation, and onboarding checklist."""
        # Surveys
        surveys_resp = self.client.get("/surveys", headers=self.auth_header(self.emp_token))
        self.assertEqual(surveys_resp.status_code, 200)
        surveys = surveys_resp.json()
        self.assertGreaterEqual(len(surveys), 1)

        survey_id = surveys[0]["id"]
        results_resp = self.client.get(f"/surveys/{survey_id}/results", headers=self.auth_header(self.hr_token))
        self.assertEqual(results_resp.status_code, 200)
        res_data = results_resp.json()
        self.assertIn("score_distribution", res_data)
        self.assertIn("sentiment_distribution", res_data)

        # Onboarding
        emp_profile = self.client.get("/auth/me", headers=self.auth_header(self.emp_token)).json()
        emp_id = emp_profile["employee_id"]

        onboarding_resp = self.client.get(f"/onboarding/{emp_id}", headers=self.auth_header(self.emp_token))
        self.assertEqual(onboarding_resp.status_code, 200)
        ob_data = onboarding_resp.json()
        self.assertIn("completion_rate_percent", ob_data)
        self.assertGreaterEqual(len(ob_data["tasks"]), 1)

        task_id = ob_data["tasks"][0]["id"]
        toggle_resp = self.client.put(
            f"/onboarding/tasks/{task_id}/complete?completed=true",
            headers=self.auth_header(self.emp_token)
        )
        self.assertEqual(toggle_resp.status_code, 200)
        self.assertTrue(toggle_resp.json()["is_completed"])

if __name__ == "__main__":
    unittest.main()
