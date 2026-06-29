import json

from backend.database.connection import get_db
from backend.core.logger import get_logger

logger = get_logger("sap_repository")


def store_sap_result(
    approval_token: str,
    sap_result: dict,
    order_id: int | None = None,
    batch_id: str | None = None,
    api_status: str = "SUCCESS",
    error_detail: str | None = None,
) -> None:
    with get_db() as conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO sap_order_results
                    (order_id, batch_id, approval_token, material, plant, quantity, unit,
                     sap_order_no, messages, raw_response, api_status, error_detail)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                order_id,
                batch_id,
                approval_token,
                sap_result.get("material"),
                sap_result.get("plant"),
                sap_result.get("quantity"),
                sap_result.get("unit"),
                sap_result.get("order_saved"),
                json.dumps(sap_result.get("messages", [])),
                json.dumps(sap_result),
                api_status,
                error_detail,
            ))
            conn.commit()
            logger.info(f"SAP result stored | token={approval_token} order={order_id} batch={batch_id}")
        except Exception as e:
            logger.error(f"store_sap_result failed: {e}")
            raise
