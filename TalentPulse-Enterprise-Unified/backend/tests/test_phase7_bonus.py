import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.survey import EngagementSurvey

class TestPhase7BonusFeatures(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

        self.admin_token = self.login("admin@talentpulse.local", "Admin123!")
        self.hr_token = self.login("hr@talentpulse.local", "Hr123!")
        self.mgr_token = self.login("manager@talentpulse.local", "Manager123!")
        self.emp_token = self.login("employee@talentpulse.local", "Employee123!")

        db = SessionLocal()
        survey = db.query(EngagementSurvey).first()
        self.sample_survey_id = survey.id if survey else 1
        db.close()

    def login(self, email, password):
        resp = self.client.post("/auth/login", json={"email": email, "password": password}, headers={"x-bypass-employee-block": "true"})
        assert resp.status_code == 200, f"Login failed for {email}: {resp.text}"
        return resp.json()["access_token"]

    def auth_header(self, token):
        return {"Authorization": f"Bearer {token}"}

    def test_bonus_survey_ai_themes(self):
        """Bonus 1: Test LLM theme synthesis from survey free-text comments."""
        # HR call -> 200 OK
        resp = self.client.post(
            f"/surveys/{self.sample_survey_id}/ai-themes",
            headers=self.auth_header(self.hr_token)
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("themes_summary", data)
        self.assertTrue(len(data["themes_summary"]) > 20)

        # Employee call -> 403 Forbidden
        emp_resp = self.client.post(
            f"/surveys/{self.sample_survey_id}/ai-themes",
            headers=self.auth_header(self.emp_token)
        )
        self.assertEqual(emp_resp.status_code, 403)

    def test_bonus_exit_interview_summary(self):
        """Bonus 2: Test LLM exit interview synthesis and retention lever identification."""
        notes = (
            "Senior backend engineer leaving after 2.8 years. Cited high overtime deployments on weekends, "
            "lack of promo to Lead Engineer, and a 35% higher offer from a remote Bangalore firm. "
            "Loved team culture in Vizag, but felt career progression stalled."
        )

        resp = self.client.post(
            "/ai/exit-summary",
            json={
                "notes": notes,
                "job_title": "Senior Software Engineer",
                "department": "Software Engineering"
            },
            headers=self.auth_header(self.hr_token)
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn(data["mode"], ("live", "offline"))
        # Exit interviews are sensitive: managers must not be able to run them.
        mgr_resp = self.client.post("/ai/exit-summary", json={"notes": notes}, headers=self.auth_header(self.mgr_token))
        self.assertEqual(mgr_resp.status_code, 403)
        self.assertIn("exit_summary", data)
        self.assertTrue(len(data["exit_summary"]) > 30)

    def test_bonus_chat_style_notifications(self):
        """Bonus 3: Test user retrieval of seeded chat-style system notifications."""
        resp = self.client.get("/notifications/my", headers=self.auth_header(self.emp_token))
        self.assertEqual(resp.status_code, 200)
        notes = resp.json()
        self.assertGreaterEqual(len(notes), 1)
        self.assertIn("title", notes[0])
        self.assertIn("message", notes[0])

if __name__ == "__main__":
    unittest.main()
