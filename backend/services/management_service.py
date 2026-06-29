from backend.repositories.user_repository import get_user
from backend.repositories.management_repository import (
    get_queue,
    get_history,
    get_order_for_reapproval,
    mark_reapproved,
    get_batch_queue as _get_batch_queue,
)
from backend.repositories.audit_repository import log_action
from backend.core.logger import get_logger
from backend.utils.exceptions import OrderNotFoundError, ReApprovalLimitError, AppError

logger = get_logger("management_service")


def _get_manager_email(employee_id: str) -> str:
    user = get_user(employee_id)
    if not user or not user.get("email"):
        raise AppError(f"Manager email not configured for {employee_id}")
    return user["email"]


def approval_queue(employee_id: str) -> list[dict]:
    email = _get_manager_email(employee_id)
    return get_queue(email)


def batch_queue(employee_id: str) -> list[dict]:
    email = _get_manager_email(employee_id)
    return _get_batch_queue(email)


def approval_history(employee_id: str, status_filter: str | None = None) -> list[dict]:
    email = _get_manager_email(employee_id)
    return get_history(email, status_filter)


def re_approve_db(token: str, manager_employee_id: str) -> dict:
    """Mark order as re-approved in DB and return the order. Fast — no SAP call."""
    order = get_order_for_reapproval(token)
    if not order:
        raise OrderNotFoundError(f"No order found for token: {token}")

    if order["status"] != "REJECTED":
        raise AppError(f"Only REJECTED orders can be re-approved. Current status: {order['status']}")

    if order["re_approval_count"] >= 1:
        raise ReApprovalLimitError("This order has already been re-approved once. No further re-approvals allowed.")

    manager_email = _get_manager_email(manager_employee_id)
    mark_reapproved(token, manager_email)
    log_action("ORDER_REAPPROVED", employee_id=manager_employee_id,
               entity="ORDER", entity_id=token)
    return order
