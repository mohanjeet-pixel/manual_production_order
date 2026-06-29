"""
Login endpoint tests — /login

Real DB is used for integration-level tests (test user seeded in fixture).
validate_user is mocked for edge cases (deactivated, DB error) that are
awkward to reproduce via real DB state.

Run:
    pytest tests/test_login.py -v
"""

import bcrypt
import pytest
from unittest.mock import patch
from jose import jwt

from backend.core.config import JWT_SECRET, JWT_ALGORITHM
from backend.core.security import hash_password
from backend.database.connection import get_db

# ---------------------------------------------------------------------------
# Seed a dedicated login-test user with a known bcrypt hash
# ---------------------------------------------------------------------------

LOGIN_TEST_ID       = "LGNTST01"
LOGIN_TEST_PASSWORD = "TestPass123!"
LOGIN_TEST_ROLE     = "OPERATOR"


@pytest.fixture(scope="module")
def login_user(client):
    """Insert a login-test user with a real bcrypt hash; clean up after module."""
    hashed = hash_password(LOGIN_TEST_PASSWORD)
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (employee_id, password_hash, full_name, email, role, is_active)
            VALUES (%s, %s, 'Login Test User', 'lgntst01@test.com', %s, TRUE)
            ON CONFLICT (employee_id) DO UPDATE SET
                password_hash = EXCLUDED.password_hash,
                is_active     = TRUE
        """, (LOGIN_TEST_ID, hashed, LOGIN_TEST_ROLE))
        conn.commit()
    yield {"employee_id": LOGIN_TEST_ID, "password": LOGIN_TEST_PASSWORD, "role": LOGIN_TEST_ROLE}
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE employee_id = %s", (LOGIN_TEST_ID,))
        conn.commit()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _post_login(client, employee_id, password):
    return client.post("/login", json={"employee_id": employee_id, "password": password})


# ---------------------------------------------------------------------------
# 1. Happy path
# ---------------------------------------------------------------------------

class TestLoginSuccess:

    def test_returns_200(self, client, login_user):
        resp = _post_login(client, login_user["employee_id"], login_user["password"])
        assert resp.status_code == 200

    def test_success_flag_is_true(self, client, login_user):
        body = _post_login(client, login_user["employee_id"], login_user["password"]).json()
        assert body["success"] is True

    def test_response_contains_employee_id(self, client, login_user):
        body = _post_login(client, login_user["employee_id"], login_user["password"]).json()
        assert body["employee_id"] == login_user["employee_id"]

    def test_response_contains_correct_role(self, client, login_user):
        body = _post_login(client, login_user["employee_id"], login_user["password"]).json()
        assert body["role"] == login_user["role"]

    def test_response_contains_token(self, client, login_user):
        body = _post_login(client, login_user["employee_id"], login_user["password"]).json()
        assert body.get("token") is not None
        assert len(body["token"]) > 10

    def test_success_message(self, client, login_user):
        body = _post_login(client, login_user["employee_id"], login_user["password"]).json()
        assert "success" in body["message"].lower() or body["message"] != ""


# ---------------------------------------------------------------------------
# 2. JWT token validity
# ---------------------------------------------------------------------------

class TestLoginToken:

    def test_token_is_valid_jwt(self, client, login_user):
        body = _post_login(client, login_user["employee_id"], login_user["password"]).json()
        payload = jwt.decode(body["token"], JWT_SECRET, algorithms=[JWT_ALGORITHM])
        assert payload is not None

    def test_token_sub_matches_employee_id(self, client, login_user):
        body = _post_login(client, login_user["employee_id"], login_user["password"]).json()
        payload = jwt.decode(body["token"], JWT_SECRET, algorithms=[JWT_ALGORITHM])
        assert payload["sub"] == login_user["employee_id"]

    def test_token_role_matches_user_role(self, client, login_user):
        body = _post_login(client, login_user["employee_id"], login_user["password"]).json()
        payload = jwt.decode(body["token"], JWT_SECRET, algorithms=[JWT_ALGORITHM])
        assert payload["role"] == login_user["role"]

    def test_token_has_expiry(self, client, login_user):
        body = _post_login(client, login_user["employee_id"], login_user["password"]).json()
        payload = jwt.decode(body["token"], JWT_SECRET, algorithms=[JWT_ALGORITHM])
        assert "exp" in payload


# ---------------------------------------------------------------------------
# 3. Wrong password
# ---------------------------------------------------------------------------

class TestLoginWrongPassword:

    def test_wrong_password_returns_200(self, client, login_user):
        resp = _post_login(client, login_user["employee_id"], "WrongPass!")
        assert resp.status_code == 200

    def test_wrong_password_success_false(self, client, login_user):
        body = _post_login(client, login_user["employee_id"], "WrongPass!").json()
        assert body["success"] is False

    def test_wrong_password_no_token(self, client, login_user):
        body = _post_login(client, login_user["employee_id"], "WrongPass!").json()
        assert body.get("token") is None

    def test_wrong_password_failure_message(self, client, login_user):
        body = _post_login(client, login_user["employee_id"], "WrongPass!").json()
        assert body["message"] != ""

    def test_empty_password_fails(self, client, login_user):
        body = _post_login(client, login_user["employee_id"], "").json()
        assert body["success"] is False


# ---------------------------------------------------------------------------
# 4. Unknown employee
# ---------------------------------------------------------------------------

class TestLoginUnknownEmployee:

    def test_unknown_employee_returns_200(self, client):
        resp = _post_login(client, "NOBODY999", "somepassword")
        assert resp.status_code == 200

    def test_unknown_employee_success_false(self, client):
        body = _post_login(client, "NOBODY999", "somepassword").json()
        assert body["success"] is False

    def test_unknown_employee_no_token(self, client):
        body = _post_login(client, "NOBODY999", "somepassword").json()
        assert body.get("token") is None

    def test_unknown_employee_failure_message(self, client):
        body = _post_login(client, "NOBODY999", "somepassword").json()
        assert body["message"] != ""


# ---------------------------------------------------------------------------
# 5. Deactivated account  (mock validate_user to return None for deactivated)
# ---------------------------------------------------------------------------

class TestLoginDeactivatedAccount:

    def test_deactivated_account_success_false(self, client, login_user):
        """Patch validate_user to simulate a deactivated-account rejection."""
        with patch("backend.api.auth.validate_user", return_value=None):
            body = _post_login(client, login_user["employee_id"], login_user["password"]).json()
        assert body["success"] is False

    def test_deactivated_account_no_token(self, client, login_user):
        with patch("backend.api.auth.validate_user", return_value=None):
            body = _post_login(client, login_user["employee_id"], login_user["password"]).json()
        assert body.get("token") is None

    def test_deactivated_account_via_real_db(self, client, login_user):
        """Set is_active=FALSE in the DB and expect rejection."""
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE users SET is_active = FALSE WHERE employee_id = %s",
                (login_user["employee_id"],)
            )
            conn.commit()
        try:
            body = _post_login(client, login_user["employee_id"], login_user["password"]).json()
            assert body["success"] is False
            assert body.get("token") is None
        finally:
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute(
                    "UPDATE users SET is_active = TRUE WHERE employee_id = %s",
                    (login_user["employee_id"],)
                )
                conn.commit()


# ---------------------------------------------------------------------------
# 6. Input validation (Pydantic / FastAPI 422 errors)
# ---------------------------------------------------------------------------

class TestLoginInputValidation:

    def test_missing_employee_id_returns_422(self, client):
        resp = client.post("/login", json={"password": "somepassword"})
        assert resp.status_code == 422

    def test_missing_password_returns_422(self, client):
        resp = client.post("/login", json={"employee_id": "EMP001"})
        assert resp.status_code == 422

    def test_empty_body_returns_422(self, client):
        resp = client.post("/login", json={})
        assert resp.status_code == 422

    def test_null_employee_id_returns_422(self, client):
        resp = client.post("/login", json={"employee_id": None, "password": "pass"})
        assert resp.status_code == 422

    def test_null_password_returns_422(self, client):
        resp = client.post("/login", json={"employee_id": "EMP001", "password": None})
        assert resp.status_code == 422

    def test_non_json_body_returns_422(self, client):
        resp = client.post("/login", content="not-json",
                           headers={"Content-Type": "application/json"})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 7. Case sensitivity
# ---------------------------------------------------------------------------

class TestLoginCaseSensitivity:

    def test_lowercase_employee_id_fails(self, client, login_user):
        """Employee IDs are stored uppercase; lowercase must not authenticate."""
        body = _post_login(client, login_user["employee_id"].lower(), login_user["password"]).json()
        assert body["success"] is False

    def test_mixed_case_employee_id_fails(self, client, login_user):
        mixed = login_user["employee_id"].capitalize()
        body = _post_login(client, mixed, login_user["password"]).json()
        assert body["success"] is False


# ---------------------------------------------------------------------------
# 8. Response schema completeness
# ---------------------------------------------------------------------------

class TestLoginResponseSchema:

    def test_success_response_has_all_fields(self, client, login_user):
        body = _post_login(client, login_user["employee_id"], login_user["password"]).json()
        assert "success" in body
        assert "employee_id" in body
        assert "role" in body
        assert "token" in body
        assert "message" in body

    def test_failure_response_has_success_and_message(self, client):
        body = _post_login(client, "NOBODY", "wrong").json()
        assert "success" in body
        assert "message" in body

    def test_failure_response_employee_id_is_null(self, client):
        body = _post_login(client, "NOBODY", "wrong").json()
        assert body.get("employee_id") is None

    def test_failure_response_role_is_null(self, client):
        body = _post_login(client, "NOBODY", "wrong").json()
        assert body.get("role") is None

    def test_failure_response_token_is_null(self, client):
        body = _post_login(client, "NOBODY", "wrong").json()
        assert body.get("token") is None
