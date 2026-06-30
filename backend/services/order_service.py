from backend.repositories.approval_repository import get_approver_email
from backend.repositories.order_repository import insert_order, get_orders_by_employee
from backend.repositories.audit_repository import log_action
from backend.repositories.plant_repository import get_price_for_part
from backend.repositories.user_repository import get_user
from backend.services.approval_service import generate_token
from backend.core.config import APP_URL
from backend.core.logger import get_logger
from backend.core.constants import STATUS_PENDING
from backend.utils.exceptions import AppError

logger = get_logger("order_service")


class PlantPartError(AppError):
    status_code = 422


def save_order(employee_id: str, plant: str, part_no: str, quantity: float, remark: str | None = None) -> tuple[str, str, str]:
    """Validate plant+part, save order, return (approver_email, subject, body) for background email."""
    price = get_price_for_part(part_no, plant)
    if price is None:
        log_action("ORDER_CREATED", status="FAILURE", employee_id=employee_id,
                   entity="ORDER", detail=f"Part {part_no} not available in plant {plant}")
        raise PlantPartError(
            f"Part '{part_no}' not found for plant '{plant}'."
        )

    value = float(quantity) * price
    approver = get_approver_email(value)
    token = generate_token()

    insert_order(employee_id, plant, part_no, quantity, value, price, STATUS_PENDING, token, approver, remark=remark)

    log_action("ORDER_CREATED", employee_id=employee_id, entity="ORDER",
               entity_id=part_no, detail=f"plant={plant} qty={quantity} value={value:.2f}")

    user = get_user(employee_id)
    full_name = user["full_name"] if user and user.get("full_name") else employee_id
    requestor_display = f"{employee_id} ({full_name})"

    action_link = f"{APP_URL}/email/action/{token}"

    remark_line = f"<b>Remark    :</b> {remark}<br>" if remark else ""

    body = f"""
    <h2>Manual Production Order &#x2014; Approval Required</h2>

    <b>Requestor :</b> {requestor_display}<br>
    <b>Plant     :</b> {plant}<br>
    <b>Part No   :</b> {part_no}<br>
    <b>Quantity  :</b> {quantity}<br>
    <b>Value     :</b> &#x20B9;{value:,.2f}<br>
    {remark_line}<br>

    <p style="color:#64748b;font-size:13px;">
      Click the button below to review this order and take action.
      The approve / reject options will be hidden once a decision has been made.
    </p><br>

    <a href="{action_link}" style="text-decoration:none;">
        <button style="background:#1a3c5e;color:white;padding:14px 32px;
                       font-size:15px;font-weight:bold;border:none;border-radius:6px;
                       cursor:pointer;">
            Review &amp; Take Action &#x2192;
        </button>
    </a>
    """

    logger.info(f"Order saved | approver={approver} token={token} value={value}")
    return approver, "Manual Production Order — Approval Required", body


def get_orders(employee_id: str) -> list[dict]:
    return get_orders_by_employee(employee_id)
