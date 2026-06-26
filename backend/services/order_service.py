import psycopg2

from backend.services.mail_service import send_mail
from backend.services.approval_service import generate_token
from backend.core.config import APP_URL

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


def get_approver_email(value):

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        SELECT approver_email
        FROM approval_matrix
        WHERE %s BETWEEN min_value AND max_value
    """, (value,))

    row = cur.fetchone()

    cur.close()
    conn.close()

    if row:
        return row[0]

    raise Exception("No Approver Found")


def save_order(employee_id, plant, part_no, quantity):

    price = get_part_price(part_no)

    if price is None:
        raise Exception(f"Part No {part_no} not found.")

    value = float(quantity) * float(price)

    approver = get_approver_email(value)

    token = generate_token()

    status = "PENDING"

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
            price,
            status,
            approval_token,
            approver_email
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
    """,
    (
        employee_id,
        plant,
        part_no,
        quantity,
        value,
        price,
        status,
        token,
        approver
    ))

    conn.commit()

    cur.close()
    conn.close()

    approve_link = f"{APP_URL}/approve/{token}"
    reject_link = f"{APP_URL}/reject/{token}"

    body = f"""
    <h2>Manual Production Order Approval</h2>

    <b>Employee :</b> {employee_id}<br>
    <b>Plant :</b> {plant}<br>
    <b>Part :</b> {part_no}<br>
    <b>Quantity :</b> {quantity}<br>
    <b>Value :</b> ₹{value:,.2f}<br><br>

    <a href="{approve_link}">
        <button style="background:green;color:white;padding:10px;">
            APPROVE
        </button>
    </a>

    <br><br>

    <a href="{reject_link}">
        <button style="background:red;color:white;padding:10px;">
            REJECT
        </button>
    </a>
    """

    print("========== EMAIL DEBUG ==========")
    print("Approver :", approver)
    print("Token    :", token)
    print("Value    :", value)

    send_mail(
        approver,
        "Manual Production Order Approval",
        body
    )


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
            value,
            COALESCE(status,'PENDING'),
            approved_by,
            approved_at
        FROM manual_production_orders
        WHERE employee_id=%s
        ORDER BY id DESC
    """, (employee_id,))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    orders = []

    for r in rows:

        orders.append({

            "ID": r[0],
            "Employee": r[1],
            "Plant": r[2],
            "Part No": r[3],
            "Quantity": r[4],
            "Unit Price": r[5],
            "Value": r[6],
            "Status": r[7],
            "Approved By": r[8] if r[8] else "",
            "Approved At": str(r[9]) if r[9] else ""

        })

    return orders
