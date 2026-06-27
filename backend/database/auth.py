from backend.repositories.user_repository import get_user
from backend.repositories.audit_repository import log_action
from backend.core.security import verify_password
from backend.core.logger import get_logger

logger = get_logger("auth")


def validate_user(employee_id: str, password: str) -> bool:
    try:
        row = get_user(employee_id)
        if not row:
            logger.warning(f"Login attempt — unknown employee: {employee_id}")
            log_action("LOGIN_FAILURE", status="FAILURE", employee_id=employee_id,
                       entity="USER", detail="Employee not found")
            return False

        if not verify_password(password, row[1]):
            logger.warning(f"Login attempt — wrong password: {employee_id}")
            log_action("LOGIN_FAILURE", status="FAILURE", employee_id=employee_id,
                       entity="USER", detail="Wrong password")
            return False

        log_action("LOGIN_SUCCESS", employee_id=employee_id, entity="USER")
        return True

    except Exception as e:
        logger.error(f"validate_user error: {e}")
        log_action("LOGIN_FAILURE", status="ERROR", employee_id=employee_id,
                   entity="USER", detail=str(e))
        return False
