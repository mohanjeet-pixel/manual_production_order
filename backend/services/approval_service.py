import uuid

from backend.repositories.order_repository import update_order_status
from backend.repositories.audit_repository import log_action
from backend.core.constants import STATUS_APPROVED, STATUS_REJECTED
from backend.core.logger import get_logger

logger = get_logger("approval_service")


def generate_token() -> str:
    return str(uuid.uuid4())


def approve_order(token: str):
    logger.info(f"Approving order | token={token}")
    update_order_status(token, STATUS_APPROVED)
    log_action("ORDER_APPROVED", entity="ORDER", entity_id=token)


def reject_order(token: str):
    logger.info(f"Rejecting order | token={token}")
    update_order_status(token, STATUS_REJECTED)
    log_action("ORDER_REJECTED", entity="ORDER", entity_id=token)
