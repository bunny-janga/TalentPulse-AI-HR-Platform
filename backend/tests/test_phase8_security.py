"""Regression tests for the security and correctness fixes."""
import os
import unittest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from app.main import app


class TestPhase8Security(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def login(self, email, password):
        r = self.client.post("/auth/login", json={"email": email, "password": password})
        self.assertEqual(r.status_code, 200, r.text)
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    # ---- authentication ----
    def test_login_is_exact_and_case_sensitive(self):
        # The old code accepted lower-cased passwords and hard-coded fallbacks.
        for bad in ("admin123!", "ADMIN123!", "Admin123! "):
            r = self.client.post("/auth/login", json={"email": "admin@talentpulse.local", "password": bad})
            self.assertEqual(r.status_code, 401, bad)

    # ---- database browser ----
    def test_db_browser_requires_admin(self):
        self.assertIn(self.client.post("/db/query", json={"sql": "SELECT 1"}).status_code, (401, 403))
        emp = self.login("employee@talentpulse.local", "Employee123!")
        self.assertEqual(self.client.post("/db/query", json={"sql": "SELECT 1"}, headers=emp).status_code, 403)

    def test_db_browser_is_read_only_and_hides_passwords(self):
        admin = self.login("admin@talentpulse.local", "Admin123!")
        ok = self.client.post("/db/query", json={"sql": "SELECT email, hashed_password, initial_password FROM users LIMIT 3"}, headers=admin)
        self.assertEqual(ok.status_code, 200, ok.text)
        for row in ok.json()["rows"]:
            self.assertIsNone(row[1])
            self.assertIsNone(row[2])
        for sql in ("DELETE FROM users", "SELECT 1; DROP TABLE users", "PRAGMA table_info(users)", "UPDATE users SET role='admin'"):
            r = self.client.post("/db/query", json={"sql": sql}, headers=admin)
            self.assertEqual(r.status_code, 400, sql)

    # ---- privacy ----
    def test_salary_is_hidden_from_other_employees(self):
        emp = self.login("employee@talentpulse.local", "Employee123!")
        rows = self.client.get("/employees", headers=emp).json()
        me = self.client.get("/auth/me", headers=emp).json()
        for e in rows:
            if e["user_id"] != me["id"]:
                self.assertIsNone(e["salary"])
                self.assertIsNone(e["performance_rating"])
        hr = self.login("hr@talentpulse.local", "Hr123!")
        self.assertIsNotNone(self.client.get("/employees", headers=hr).json()[0]["salary"])

    def test_password_vault_removed(self):
        admin = self.login("admin@talentpulse.local", "Admin123!")
        r = self.client.post("/admin/employees/passwords", json={"admin_password": "Admin123!"}, headers=admin)
        self.assertIn(r.status_code, (404, 405))

    # ---- leave rules ----
    def test_leave_rejects_bad_input_and_overlap(self):
        emp = self.login("employee@talentpulse.local", "Employee123!")
        today = date.today()
        body = {"leave_type": "Not A Type", "start_date": (today + timedelta(days=30)).isoformat(), "end_date": (today + timedelta(days=31)).isoformat(), "reason": "test"}
        self.assertEqual(self.client.post("/leave/apply", json=body, headers=emp).status_code, 422)
        body.update(leave_type="Unpaid Leave", start_date=(today - timedelta(days=3)).isoformat(), end_date=today.isoformat())
        self.assertEqual(self.client.post("/leave/apply", json=body, headers=emp).status_code, 422)  # past, not sick
        bal = self.client.get("/leave/balance", headers=emp)
        self.assertEqual(bal.status_code, 200)
        self.assertEqual({b["leave_type"] for b in bal.json()["balances"]}, {"Casual Leave", "Sick Leave", "Earned Leave"})

    # ---- policy upload ----
    def test_policy_upload_cannot_escape_upload_dir(self):
        hr = self.login("hr@talentpulse.local", "Hr123!")
        files = {"file": ("../../evil.txt", b"Travel policy: economy class for flights under six hours, approvals by manager.", "text/plain")}
        r = self.client.post("/policies/upload", data={"title": "Traversal probe", "category": "Test"}, files=files, headers=hr)
        self.assertEqual(r.status_code, 201, r.text)
        path = r.json().get("file_path") or ""
        self.assertNotIn("..", os.path.basename(path))
        self.assertEqual(self.client.delete(f"/policies/{r.json()['id']}", headers=hr).status_code, 204)

    def test_policy_upload_rejects_wrong_type(self):
        hr = self.login("hr@talentpulse.local", "Hr123!")
        r = self.client.post("/policies/upload", data={"title": "Bad file", "category": "Test"}, files={"file": ("x.exe", b"MZ....", "application/octet-stream")}, headers=hr)
        self.assertEqual(r.status_code, 415)

    # ---- drafts hidden from employees ----
    def test_employee_does_not_see_draft_reviews(self):
        emp = self.login("employee@talentpulse.local", "Employee123!")
        for rev in self.client.get("/reviews/my", headers=emp).json():
            self.assertEqual(rev["status"], "COMPLETED")


if __name__ == "__main__":
    unittest.main()
