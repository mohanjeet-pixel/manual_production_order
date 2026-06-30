import uuid

from backend.repositories.order_repository import update_order_status, get_order_by_token
from backend.repositories.audit_repository import log_action
from backend.services.sap_service import call_sap_and_normalize
from backend.repositories.sap_repository import store_sap_result
from backend.core.constants import STATUS_APPROVED, STATUS_REJECTED
from backend.core.logger import get_logger

logger = get_logger("approval_service")


def generate_token() -> str:
    return str(uuid.uuid4())


def approve_order_db(token: str) -> dict | None:
    """Update order status to APPROVED and return the order.
    Returns None if the order was already processed — caller must skip SAP in that case."""
    logger.info(f"Approving order | token={token}")
    order = get_order_by_token(token)
    if not order:
        raise ValueError(f"No order found for token: {token}")
    if order["status"] != "PENDING":
        logger.warning(f"approve_order_db: order already {order['status']} | token={token}")
        return None
    update_order_status(token, STATUS_APPROVED)
    log_action("ORDER_APPROVED", entity="ORDER", entity_id=token)
    return order


def submit_to_sap(token: str, order: dict) -> None:
    """Call SAP and store result. Runs as a background task — may take up to 5 minutes."""
    try:
        sap_result = call_sap_and_normalize(order["part_no"], order["plant"], order["quantity"])
        store_sap_result(token, sap_result, order_id=order["id"])
        log_action("SAP_ORDER_SUBMITTED", entity="ORDER", entity_id=token,
                   detail=sap_result.get("order_saved"))
        logger.info(f"SAP submission complete | token={token}")
    except Exception as e:
        logger.error(f"SAP submission failed | token={token}: {e}")
        store_sap_result(token, {}, order_id=order["id"],
                         api_status="FAILURE", error_detail=str(e))
        log_action("SAP_ORDER_FAILED", status="FAILURE", entity="ORDER",
                   entity_id=token, detail=str(e))


def reject_order(token: str) -> None:
    order = get_order_by_token(token)
    if not order:
        raise ValueError(f"No order found for token: {token}")
    if order["status"] != "PENDING":
        logger.warning(f"reject_order: order already {order['status']} — skipping | token={token}")
        return
    logger.info(f"Rejecting order | token={token}")
    update_order_status(token, STATUS_REJECTED)
    log_action("ORDER_REJECTED", entity="ORDER", entity_id=token)
