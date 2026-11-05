import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.review import PerformanceReview

class TestPhase5GenAI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

        # Log in demo accounts
        self.admin_token = self.login("admin@talentpulse.local", "Admin123!")
        self.hr_token = self.login("hr@talentpulse.local", "Hr123!")
        self.mgr_token = self.login("manager@talentpulse.local", "Manager123!")
        self.mgr2_token = self.login("manager2@talentpulse.local", "Manager123!")
        self.emp_token = self.login("employee@talentpulse.local", "Employee123!")

        # Find a review ID belonging to manager's direct report
        db = SessionLocal()
        from app.models.user import User
        mgr = db.query(User).filter(User.email == "manager@talentpulse.local").first()
        rev = db.query(PerformanceReview).filter(PerformanceReview.reviewer_id == mgr.id).first()
        if not rev:
            rev = db.query(PerformanceReview).first()
        self.sample_review_id = rev.id
        db.close()

    def login(self, email, password):
        resp = self.client.post("/auth/login", json={"email": email, "password": password}, headers={"x-bypass-employee-block": "true"})
        assert resp.status_code == 200, f"Login failed for {email}: {resp.text}"
        return resp.json()["access_token"]

    def auth_header(self, token):
        return {"Authorization": f"Bearer {token}"}

    def test_rag_helpdesk_covered_policy(self):
        """GenAI 1: Test Q&A on covered policy with document citation and sources."""
        query = "How many days of Paternity Leave are granted to new fathers?"
        resp = self.client.post(
            "/chat/ask",
            json={"query": query},
            headers=self.auth_header(self.emp_token)
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["query"], query)
        self.assertIn("10", data["answer"])
        self.assertGreaterEqual(len(data["sources"]), 1)
        self.assertTrue(any("Leave Policy" in s["title"] for s in data["sources"]))

    def test_rag_helpdesk_uncovered_policy(self):
        """GenAI 1: Test strict grounded rule - reply 'not covered in current policy' when absent."""
        query = "What is the reimbursement limit for scuba diving gear and surfboards in Vizag beach?"
        resp = self.client.post(
            "/chat/ask",
            json={"query": query},
            headers=self.auth_header(self.emp_token)
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("not covered in current policy", data["answer"].lower())

    def test_chat_history_persistence(self):
        """Verify chat exchanges are saved in database and accessible via /chat/history."""
        # Send a chat message first so history contains at least 1 record
        self.client.post(
            "/chat/ask",
            json={"query": "How many days of casual leave do I get?"},
            headers=self.auth_header(self.emp_token)
        )
        resp = self.client.get("/chat/history", headers=self.auth_header(self.emp_token))
        self.assertEqual(resp.status_code, 200)
        history = resp.json()
        self.assertGreaterEqual(len(history), 1)

    def test_ai_assisted_review_drafting(self):
        """GenAI 2: Test turning manager bullet notes into a structured review draft."""
        bullet_notes = """
        - Delivered the notification service 3 days before sprint deadline.
        - High code quality with 95% unit test coverage.
        - Sometimes gets quiet during client sync calls, could present architecture more proactively.
        - Next goal: mentor the incoming intern and spearhead the Docker container migration.
        """

        # 1. Direct manager drafts review -> 200 OK
        resp = self.client.post(
            f"/reviews/{self.sample_review_id}/ai-draft",
            json={"bullet_notes": bullet_notes},
            headers=self.auth_header(self.mgr_token)
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(len(data["draft_review"]) > 50)
        self.assertTrue(len(data["strengths"]) > 10)
        self.assertTrue(len(data["growth_areas"]) > 10)
        self.assertTrue(len(data["goals"]) > 10)

        # 2. Unrelated manager attempting to draft review for another manager's report -> 403 Forbidden
        unrelated_resp = self.client.post(
            f"/reviews/{self.sample_review_id}/ai-draft",
            json={"bullet_notes": bullet_notes},
            headers=self.auth_header(self.mgr2_token)
        )
        self.assertEqual(unrelated_resp.status_code, 403)

if __name__ == "__main__":
    unittest.main()
