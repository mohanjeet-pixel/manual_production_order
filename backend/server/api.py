from fastapi import FastAPI

import psycopg2

from backend.order_service import DB_CONFIG

app = FastAPI()


@app.get("/approve/{token}")

def approve(token):

    conn = psycopg2.connect(**DB_CONFIG)

    cur = conn.cursor()

    cur.execute("""
        UPDATE manual_production_orders
        SET
            status='APPROVED',
            approved_at=NOW()
        WHERE approval_token=%s
    """, (token,))

    conn.commit()

    cur.close()

    conn.close()

    return {
        "message":"Order Approved Successfully"
    }


@app.get("/reject/{token}")

def reject(token):

    conn = psycopg2.connect(**DB_CONFIG)

    cur = conn.cursor()

    cur.execute("""
        UPDATE manual_production_orders
        SET
            status='REJECTED',
            approved_at=NOW()
        WHERE approval_token=%s
    """, (token,))

    conn.commit()

    cur.close()

    conn.close()

    return {
        "message":"Order Rejected Successfully"
    }