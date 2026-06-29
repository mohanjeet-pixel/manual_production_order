"""
Integration tests for the SAP approval flow.

Real DB is used (no DB mocking).
SAP HTTP calls are mocked — we don't have real SAP credentials in CI.

Run:
    pytest tests/test_sap_approval.py -v
"""
from unittest.mock import MagicMock, patch

import pytest

from backend.database.connection import get_db
from tests.conftest import SAP_MOCK_RESPONSE


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_sap_post(monkeypatch, response_body: dict | None = None, status_code: int = 200):
    """Patch requests.post inside sap_service to return a controlled response."""
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = response_body or SAP_MOCK_RESPONSE
    mock.raise_for_status = MagicMock()  # no-op on success
    monkeypatch.setattr("backend.services.sap_service.requests.post", lambda *a, **kw: mock)
    return mock


def _fetch_sap_result(approval_token: str) -> dict | None:
    """Query sap_order_results by approval token."""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT sap_order_no, api_status, material, plant FROM sap_order_results WHERE approval_token = %s",
            (approval_token,)
        )
        row = cur.fetchone()
        if not row:
            return None
        return {"sap_order_no": row[0], "api_status": row[1], "material": row[2], "plant": row[3]}


def _fetch_order_status(approval_token: str) -> str | None:
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT status FROM manual_production_orders WHERE approval_token = %s",
            (approval_token,)
        )
        row = cur.fetchone()
        return row[0] if row else None


# ---------------------------------------------------------------------------
# Standalone order tests
# ---------------------------------------------------------------------------

class TestApproveOrder:

    def test_approve_returns_sap_normalized_response(self, client, pending_order_token, monkeypatch):
        _mock_sap_post(monkeypatch)
        resp = client.get(f"/approve/{pending_order_token}")

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "SAP" in body["message"]

        data = body["data"]
        assert data["material"] == "8000116"
        assert data["plant"] == "1000"
        assert data["quantity"] == 10
        assert data["unit"] == "nos"
        assert data["order_saved"] == "Order number 12806611 saved"
        assert len(data["messages"]) == 3

    def test_approve_updates_order_status_to_approved(self, client, pending_order_token, monkeypatch):
        _mock_sap_post(monkeypatch)
        client.get(f"/approve/{pending_order_token}")

        status = _fetch_order_status(pending_order_token)
        assert status == "APPROVED"

    def test_approve_stores_sap_result_in_db(self, client, pending_order_token, monkeypatch):
        _mock_sap_post(monkeypatch)
        client.get(f"/approve/{pending_order_token}")

        row = _fetch_sap_result(pending_order_token)
        assert row is not None
        assert row["api_status"] == "SUCCESS"
        assert row["sap_order_no"] == "Order number 12806611 saved"
        assert row["material"] == "8000116"
        assert row["plant"] == "1000"

    def test_approve_gracefully_handles_sap_failure(self, client, pending_order_token, monkeypatch):
        """Order must still be APPROVED even when SAP call fails."""
        def _raise(*a, **kw):
            raise ConnectionError("SAP unreachable")
        monkeypatch.setattr("backend.services.sap_service.requests.post", _raise)

        resp = client.get(f"/approve/{pending_order_token}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "sap_error" in body["data"]

        # Order still approved
        assert _fetch_order_status(pending_order_token) == "APPROVED"

        # Failure logged in DB
        row = _fetch_sap_result(pending_order_token)
        assert row is not None
        assert row["api_status"] == "FAILURE"

    def test_reject_does_not_call_sap(self, client, pending_order_token, monkeypatch):
        called = []
        monkeypatch.setattr(
            "backend.services.sap_service.requests.post",
            lambda *a, **kw: called.append(1),
        )
        resp = client.get(f"/reject/{pending_order_token}")

        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert called == []  # SAP was never called

        status = _fetch_order_status(pending_order_token)
        assert status == "REJECTED"

        # No SAP result row
        assert _fetch_sap_result(pending_order_token) is None

    def test_messages_structure_is_correct(self, client, pending_order_token, monkeypatch):
        _mock_sap_post(monkeypatch)
        resp = client.get(f"/approve/{pending_order_token}")
        messages = resp.json()["data"]["messages"]
        for msg in messages:
            assert "no" in msg
            assert "type" in msg
            assert "text" in msg

    def test_approve_unknown_token_returns_500(self, client):
        resp = client.get("/approve/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# Batch order tests
# ---------------------------------------------------------------------------

class TestApproveBatch:

    def test_batch_approve_calls_sap_for_each_order(self, client, pending_batch_token, monkeypatch):
        token, _ = pending_batch_token
        calls = []

        def _fake_post(*a, **kw):
            calls.append(kw.get("json") or a)
            mock = MagicMock()
            mock.json.return_value = SAP_MOCK_RESPONSE
            mock.raise_for_status = MagicMock()
            return mock

        monkeypatch.setattr("backend.services.sap_service.requests.post", _fake_post)
        resp = client.get(f"/approve/batch/{token}")

        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert len(calls) == 2  # one per order in the batch

    def test_batch_approve_stores_sap_result_per_order(self, client, pending_batch_token, monkeypatch):
        token, batch_id = pending_batch_token
        _mock_sap_post(monkeypatch)
        client.get(f"/approve/batch/{token}")

        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM sap_order_results WHERE batch_id = %s AND api_status = 'SUCCESS'",
                (batch_id,)
            )
            count = cur.fetchone()[0]
        assert count == 2

    def test_batch_reject_does_not_call_sap(self, client, pending_batch_token, monkeypatch):
        token, _ = pending_batch_token
        called = []
        monkeypatch.setattr(
            "backend.services.sap_service.requests.post",
            lambda *a, **kw: called.append(1),
        )
        resp = client.get(f"/reject/batch/{token}")
        assert resp.status_code == 200
        assert called == []
