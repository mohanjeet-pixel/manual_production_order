import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "database": "Manual_order",
    "user": "postgres",
    "password": "bull@123"
}

def get_part_price(part_no):

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        SELECT price
        FROM products
        WHERE part = %s
    """, (part_no,))

    row = cur.fetchone()

    cur.close()
    conn.close()

    if row:
        return float(row[0])

    return None

def save_order(employee_id, plant, part_no, quantity):

    price = get_part_price(part_no)

    if price is None:
        raise Exception(
            f"Part No {part_no} not found in products table"
        )

    value = float(quantity) * float(price)

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO manual_production_orders
        (
            employee_id,
            plant,
            part_no,
            quantity,
            value,
            price    
        )
        VALUES (%s,%s,%s,%s,%s,%s)
    """,
    (
        employee_id,
        plant,
        part_no,
        quantity,
        value,
        price
    ))

    conn.commit()

    cur.close()
    conn.close()

def get_orders(employee_id):

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            employee_id,
            plant,
            part_no,
            quantity,
            price,
            value
        FROM manual_production_orders
        WHERE employee_id = %s
        ORDER BY id DESC
    """, (employee_id,))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {
            "ID": r[0],
            "Employee": r[1],
            "Plant": r[2],
            "Part No": r[3],
            "Quantity": r[4],
            "Unit Price": r[5],   # <-- IMPORTANT
            "Value": r[6]
        }
        for r in rows
    ]