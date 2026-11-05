import unittest
from fastapi.testclient import TestClient
from app.main import app

class TestPhase1Auth(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_login_success_all_roles(self):
        """Verify demo credentials and JWT generation for all management roles."""
        roles_credentials = [
            ("superadmin@talentpulse.local", "super123!", "superadmin"),
            ("admin@talentpulse.local", "Admin123!", "admin"),
            ("hr@talentpulse.local", "Hr123!", "hr"),
            ("manager@talentpulse.local", "Manager123!", "manager"),
            ("employee@talentpulse.local", "Employee123!", "employee"),
        ]

        for email, password, expected_role in roles_credentials:
            response = self.client.post(
                "/auth/login",
                json={"email": email, "password": password}
            )
            self.assertEqual(response.status_code, 200, f"Failed login for {email}: {response.text}")
            data = response.json()
            self.assertIn("access_token", data)
            self.assertEqual(data["token_type"], "bearer")
            self.assertEqual(data["role"], expected_role)
            self.assertEqual(data["email"], email)

    def test_employee_login_allowed(self):
        """Verify Employee login is enabled and returns access token."""
        response = self.client.post(
            "/auth/login",
            json={"email": "employee@talentpulse.local", "password": "Employee123!"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["role"], "employee")
        self.assertIn("access_token", response.json())

    def test_login_invalid_password(self):
        """Verify login fails with invalid credentials."""
        response = self.client.post(
            "/auth/login",
            json={"email": "employee@talentpulse.local", "password": "WrongPassword!"}
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Incorrect email or password", response.json()["detail"])

    def test_auth_me_authenticated(self):
        """Verify /auth/me returns the authenticated user profile."""
        login_resp = self.client.post(
            "/auth/login",
            json={"email": "manager@talentpulse.local", "password": "Manager123!"}
        )
        token = login_resp.json()["access_token"]

        me_resp = self.client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(me_resp.status_code, 200)
        user_data = me_resp.json()
        self.assertEqual(user_data["email"], "manager@talentpulse.local")
        self.assertEqual(user_data["role"], "manager")
        self.assertEqual(user_data["full_name"], "Rajesh Varma")
        self.assertIsNotNone(user_data["employee_id"])

    def test_auth_me_unauthenticated(self):
        """Verify /auth/me rejects unauthenticated requests."""
        response = self.client.get("/auth/me")
        self.assertEqual(response.status_code, 401)

    def test_role_dependency_register_restriction(self):
        """
        Verify role-based access control on /auth/register:
        - Admin can register a new user (201 Created or 400 if already exists)
        - Employee and Manager get 403 Forbidden
        """
        emp_token = self.client.post(
            "/auth/login",
            json={"email": "employee@talentpulse.local", "password": "Employee123!"}
        ).json()["access_token"]

        bad_reg_payload = {
            "email": "intruder@talentpulse.local",
            "password": "Password123!",
            "full_name": "Intruder User",
            "role": "employee"
        }

        emp_resp = self.client.post(
            "/auth/register",
            json=bad_reg_payload,
            headers={"Authorization": f"Bearer {emp_token}"}
        )
        self.assertEqual(emp_resp.status_code, 403)
        self.assertIn("Forbidden", emp_resp.json()["detail"])

        mgr_token = self.client.post(
            "/auth/login",
            json={"email": "manager@talentpulse.local", "password": "Manager123!"}
        ).json()["access_token"]

        mgr_resp = self.client.post(
            "/auth/register",
            json=bad_reg_payload,
            headers={"Authorization": f"Bearer {mgr_token}"}
        )
        self.assertEqual(mgr_resp.status_code, 403)

        admin_token = self.client.post(
            "/auth/login",
            json={"email": "admin@talentpulse.local", "password": "Admin123!"}
        ).json()["access_token"]

        good_reg_payload = {
            "email": "new.hire99@talentpulse.local",
            "password": "Password123!",
            "full_name": "New Hire Employee",
            "role": "employee"
        }

        admin_resp = self.client.post(
            "/auth/register",
            json=good_reg_payload,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        self.assertIn(admin_resp.status_code, [201, 400])

if __name__ == "__main__":
    unittest.main()
