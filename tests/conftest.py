import uuid
import pytest
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.database.connection import get_db

# ---------------------------------------------------------------------------
# Shared SAP mock payload
# ---------------------------------------------------------------------------
SAP_MOCK_RESPONSE = {
    "MATERIAL": "8000116",
    "PLANT": "1000",
    "QUANTITY": "10",
    "MESSAGES": [
        {"MESSAGE_NO": "732", "MESSAGE_TYPE": "E",
         "MESSAGE_TEXT": "Material 8000116 in plant 1000 has been marked"},
        {"MESSAGE_NO": "520", "MESSAGE_TYPE": "E",
         "MESSAGE_TEXT": "scheduling carried out"},
        {"MESSAGE_NO": "100", "MESSAGE_TYPE": "E",
         "MESSAGE_TEXT": "Order number 12806611 saved"},
    ],
}


# ---------------------------------------------------------------------------
# FastAPI test client (uses real lifespan → real pool)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Seed minimal test records required by FK constraints.
# Uses ON CONFLICT so re-runs are idempotent.
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def seed_test_data(client):  # client must start first so the DB pool is initialised
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (employee_id, password_hash, full_name, role)
            VALUES ('TESTOP01', 'dummy_hash_not_real', 'Test Operator', 'OPERATOR')
            ON CONFLICT (employee_id) DO NOTHING
        """)
        cur.execute("""
            INSERT INTO products (part, description, price, unit, is_active)
            VALUES ('8000116', 'Test Material for SAP', 100.00, 'nos', true)
            ON CONFLICT (part) DO NOTHING
        """)
        conn.commit()
    yield
    # Clean up only the test user/product rows we own (safe to delete if no real orders)
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM users WHERE employee_id = 'TESTOP01' "
            "AND NOT EXISTS (SELECT 1 FROM manual_production_orders WHERE employee_id = 'TESTOP01' AND status != 'PENDING')"
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Factory: create a standalone pending order, yield its token, then clean up
# ---------------------------------------------------------------------------
@pytest.fixture
def pending_order_token():
    token = str(uuid.uuid4())
    order_id = None
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO manual_production_orders
                (employee_id, plant, part_no, quantity, price, status, approval_token, approver_email)
            VALUES ('TESTOP01', '1000', '8000116', 10, 100.00, 'PENDING', %s, 'approver@test.com')
            RETURNING id
        """, (token,))
        order_id = cur.fetchone()[0]
        conn.commit()
    yield token
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM sap_order_results WHERE order_id = %s", (order_id,))
        cur.execute("DELETE FROM manual_production_orders WHERE id = %s", (order_id,))
        conn.commit()


# ---------------------------------------------------------------------------
# Factory: create a batch with two orders, yield (batch_token, batch_id)
# ---------------------------------------------------------------------------
@pytest.fixture
def pending_batch_token():
    token = str(uuid.uuid4())
    batch_id = f"TESTBATCH{uuid.uuid4().hex[:6].upper()}"
    order_ids = []
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO manual_order_batches
                (batch_id, employee_id, total_value, status, approval_token, approver_email)
            VALUES (%s, 'TESTOP01', 2000.00, 'PENDING', %s, 'approver@test.com')
        """, (batch_id, token))
        for plant in ("1000", "2000"):
            cur.execute("""
                INSERT INTO manual_production_orders
                    (employee_id, plant, part_no, quantity, price, status, batch_id)
                VALUES ('TESTOP01', %s, '8000116', 10, 100.00, 'PENDING', %s)
                RETURNING id
            """, (plant, batch_id))
            order_ids.append(cur.fetchone()[0])
        conn.commit()
    yield token, batch_id
    with get_db() as conn:
        cur = conn.cursor()
        for oid in order_ids:
            cur.execute("DELETE FROM sap_order_results WHERE order_id = %s", (oid,))
        cur.execute("DELETE FROM manual_production_orders WHERE batch_id = %s", (batch_id,))
        cur.execute("DELETE FROM manual_order_batches WHERE batch_id = %s", (batch_id,))
        conn.commit()
