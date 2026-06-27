from backend.repositories.product_repository import get_part_price
from backend.repositories.approval_repository import get_approver_email
from backend.repositories.order_repository import insert_order, get_orders_by_employee
from backend.repositories.audit_repository import log_action
from backend.services.approval_service import generate_token
from backend.core.config import APP_URL
from backend.core.logger import get_logger
from backend.core.constants import STATUS_PENDING
from backend.utils.exceptions import PartNotFoundError

logger = get_logger("order_service")


def save_order(employee_id: str, plant: str, part_no: str, quantity: float) -> tuple[str, str, str]:
    """Save order to DB and return (approver_email, subject, body) for background email dispatch."""
    price = get_part_price(part_no)
    if price is None:
        log_action("ORDER_CREATED", status="FAILURE", employee_id=employee_id,
                   entity="ORDER", detail=f"Part not found: {part_no}")
        raise PartNotFoundError(f"Part No '{part_no}' not found in products.")

    value = float(quantity) * price
    approver = get_approver_email(value)
    token = generate_token()

    insert_order(employee_id, plant, part_no, quantity, value, price, STATUS_PENDING, token, approver)

    log_action("ORDER_CREATED", employee_id=employee_id, entity="ORDER",
               entity_id=part_no, detail=f"plant={plant} qty={quantity} value={value:.2f}")

    approve_link = f"{APP_URL}/approve/{token}"
    reject_link = f"{APP_URL}/reject/{token}"

    body = f"""
    <h2>Manual Production Order &#x2014; Approval Required</h2>

    <b>Employee :</b> {employee_id}<br>
    <b>Plant    :</b> {plant}<br>
    <b>Part No  :</b> {part_no}<br>
    <b>Quantity :</b> {quantity}<br>
    <b>Value    :</b> &#x20B9;{value:,.2f}<br><br>

    <a href="{approve_link}" style="text-decoration:none;">
        <button style="background:#2e7d32;color:white;padding:12px 24px;
                       font-size:14px;border:none;border-radius:4px;">APPROVE</button>
    </a>
    &nbsp;&nbsp;
    <a href="{reject_link}" style="text-decoration:none;">
        <button style="background:#c62828;color:white;padding:12px 24px;
                       font-size:14px;border:none;border-radius:4px;">REJECT</button>
    </a>
    """

    logger.info(f"Order saved | approver={approver} token={token} value={value}")
    return approver, "Manual Production Order — Approval Required", body


def get_orders(employee_id: str) -> list[dict]:
    return get_orders_by_employee(employee_id)
