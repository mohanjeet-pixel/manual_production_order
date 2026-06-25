import psycopg2
from urllib.parse import quote_plus

DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "database": "Manual_order",
    "user": "postgres",
    "password": "bull@123"
}


def validate_user(employee_id, password):
    conn = None

    try:
        conn = psycopg2.connect(**DB_CONFIG)

        cursor = conn.cursor()

        query = """
        SELECT employee_id
        FROM users
        WHERE employee_id = %s
        AND password = %s
        """

        cursor.execute(query, (employee_id, password))

        result = cursor.fetchone()

        return result is not None

    except Exception as e:
        print("Database Error:", e)
        return False

    finally:
        if conn:
            conn.close()