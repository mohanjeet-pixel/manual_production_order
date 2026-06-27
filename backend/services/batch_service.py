from backend.repositories.product_repository import get_part_price
from backend.repositories.approval_repository import get_approver_email
from backend.repositories.order_repository import insert_order
from backend.repositories.batch_repository import (
    insert_batch,
    get_batches_by_employee,
    update_batch_status,
)
from backend.repositories.audit_repository import log_action
from backend.services.approval_service import generate_token
from backend.core.config import APP_URL
from backend.core.logger import get_logger
from backend.core.constants import STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED
from backend.utils.exceptions import PartNotFoundError

logger = get_logger("batch_service")


def create_batch(employee_id: str, items: list[dict]) -> tuple[str, str, str, str]:
    """Save batch + orders to DB and return (batch_id, approver_email, subject, body)."""
    enriched = []
    for item in items:
        price = get_part_price(item["part_no"])
        if price is None:
            log_action("BATCH_CREATED", status="FAILURE", employee_id=employee_id,
                       entity="BATCH", detail=f"Part not found: {item['part_no']}")
            raise PartNotFoundError(f"Part No '{item['part_no']}' not found in products.")
        enriched.append({**item, "price": price, "value": float(item["quantity"]) * price})

    total_value = sum(i["value"] for i in enriched)
    approver = get_approver_email(total_value)
    token = generate_token()

    batch_id = insert_batch(employee_id, total_value, token, approver)

    for item in enriched:
        insert_order(
            employee_id=employee_id,
            plant=item["plant"],
            part_no=item["part_no"],
            quantity=item["quantity"],
            value=item["value"],
            price=item["price"],
            status=STATUS_PENDING,
            batch_id=batch_id,
        )

    log_action("BATCH_CREATED", employee_id=employee_id, entity="BATCH",
               entity_id=batch_id, detail=f"items={len(enriched)} total={total_value:.2f}")

    subject = f"Batch {batch_id} — Approval Required | &#x20B9;{total_value:,.2f}"
    body = _build_batch_email_body(batch_id, employee_id, enriched, total_value, token)

    logger.info(f"Batch saved | batch={batch_id} approver={approver} items={len(enriched)} total={total_value}")
    return batch_id, approver, subject, body


def _build_batch_email_body(
    batch_id: str,
    employee_id: str,
    items: list[dict],
    total_value: float,
    token: str,
) -> str:
    approve_link = f"{APP_URL}/approve/batch/{token}"
    reject_link = f"{APP_URL}/reject/batch/{token}"

    rows_html = "".join(
        f"<tr>"
        f"<td style='padding:6px;'>{i['part_no']}</td>"
        f"<td style='padding:6px;'>{i['plant']}</td>"
        f"<td style='padding:6px;text-align:right;'>{i['quantity']}</td>"
        f"<td style='padding:6px;text-align:right;'>&#x20B9;{i['price']:,.2f}</td>"
        f"<td style='padding:6px;text-align:right;'>&#x20B9;{i['value']:,.2f}</td>"
        f"</tr>"
        for i in items
    )

    return f"""
    <h2>Batch Production Order &#x2014; Approval Required</h2>

    <b>Batch ID    :</b> {batch_id}<br>
    <b>Employee    :</b> {employee_id}<br>
    <b>Total Parts :</b> {len(items)}<br>
    <b>Total Value :</b> <strong>&#x20B9;{total_value:,.2f}</strong><br><br>

    <table border="1" cellpadding="0" cellspacing="0"
           style="border-collapse:collapse;font-family:Arial,sans-serif;font-size:13px;">
        <thead>
            <tr style="background:#f0f0f0;">
                <th style="padding:8px;">Part No</th>
                <th style="padding:8px;">Plant</th>
                <th style="padding:8px;">Qty</th>
                <th style="padding:8px;">Unit Price</th>
                <th style="padding:8px;">Value</th>
            </tr>
        </thead>
        <tbody>{rows_html}</tbody>
        <tfoot>
            <tr style="background:#e8f4e8;font-weight:bold;">
                <td colspan="4" style="padding:8px;text-align:right;">Total</td>
                <td style="padding:8px;text-align:right;">&#x20B9;{total_value:,.2f}</td>
            </tr>
        </tfoot>
    </table>

    <br>
    <a href="{approve_link}" style="text-decoration:none;">
        <button style="background:#2e7d32;color:white;padding:12px 28px;
                       font-size:14px;border:none;border-radius:4px;">
            APPROVE ALL ({len(items)} orders)
        </button>
    </a>
    &nbsp;&nbsp;
    <a href="{reject_link}" style="text-decoration:none;">
        <button style="background:#c62828;color:white;padding:12px 28px;
                       font-size:14px;border:none;border-radius:4px;">
            REJECT ALL
        </button>
    </a>
    """


def get_batches(employee_id: str) -> list[dict]:
    return get_batches_by_employee(employee_id)


def approve_batch(token: str):
    logger.info(f"Approving batch | token={token}")
    update_batch_status(token, STATUS_APPROVED)
    log_action("BATCH_APPROVED", entity="BATCH", entity_id=token)


def reject_batch(token: str):
    logger.info(f"Rejecting batch | token={token}")
    update_batch_status(token, STATUS_REJECTED)
    log_action("BATCH_REJECTED", entity="BATCH", entity_id=token)
