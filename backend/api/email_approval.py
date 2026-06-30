from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse

from backend.repositories.order_repository import get_order_by_token
from backend.repositories.batch_repository import get_batch_by_token, get_batch_items_by_token
from backend.repositories.user_repository import get_user
from backend.services.approval_service import approve_order_db, reject_order, submit_to_sap
from backend.services.batch_service import approve_batch_db, submit_batch_to_sap, reject_batch
from backend.core.config import APP_URL
from backend.core.logger import get_logger

router = APIRouter(tags=["Email Approval"])
logger = get_logger("email_approval")

_STATUS_COLOR = {
    "APPROVED": "#15803d",
    "REJECTED": "#b91c1c",
    "PENDING":  "#b45309",
}

_BASE_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Segoe UI', Arial, sans-serif;
  background: #f1f5f9;
  min-height: 100vh;
  display: flex; align-items: flex-start; justify-content: center;
  padding: 40px 16px;
}
.card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0,0,0,.10);
  width: 100%; max-width: 600px;
}
.card-header {
  padding: 20px 28px;
  border-bottom: 1px solid #e2e8f0;
  display: flex; align-items: center; justify-content: space-between;
}
.card-title { font-size: 16px; font-weight: 700; color: #1a3c5e; }
.status-badge {
  font-size: 11px; font-weight: 700; letter-spacing: .6px;
  padding: 3px 10px; border-radius: 20px;
}
.badge-PENDING  { background: #fef3c7; color: #92400e; }
.badge-APPROVED { background: #dcfce7; color: #15803d; }
.badge-REJECTED { background: #fee2e2; color: #b91c1c; }
.card-body { padding: 24px 28px; }
.detail-grid {
  display: grid; grid-template-columns: 140px 1fr;
  gap: 10px 0; font-size: 14px; margin-bottom: 20px;
}
.detail-label { color: #64748b; font-weight: 600; padding: 4px 0; }
.detail-value { color: #1e293b; padding: 4px 0; }
.remark-box {
  background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px;
  padding: 10px 14px; font-size: 13px; color: #475569; margin-bottom: 20px;
}
.remark-label { font-size: 11px; font-weight: 700; color: #94a3b8;
  letter-spacing: .5px; text-transform: uppercase; margin-bottom: 4px; }
table { width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 20px; }
th { background: #f1f5f9; color: #64748b; font-weight: 600;
  padding: 8px 10px; text-align: left; border-bottom: 1px solid #e2e8f0; }
td { padding: 8px 10px; border-bottom: 1px solid #f1f5f9; color: #1e293b; }
td.num { text-align: right; }
.total-row td { font-weight: 700; background: #f0fdf4; color: #15803d; }
.action-bar {
  display: flex; gap: 12px; margin-top: 8px;
}
.btn-approve {
  flex: 1; padding: 14px; background: #15803d; color: #fff;
  border: none; border-radius: 8px; font-size: 15px; font-weight: 700;
  cursor: pointer; text-decoration: none; text-align: center;
  display: block;
}
.btn-approve:hover { background: #166534; }
.btn-reject {
  flex: 1; padding: 14px; background: #b91c1c; color: #fff;
  border: none; border-radius: 8px; font-size: 15px; font-weight: 700;
  cursor: pointer; text-decoration: none; text-align: center;
  display: block;
}
.btn-reject:hover { background: #991b1b; }
.done-banner {
  text-align: center; padding: 24px 16px;
}
.done-icon { font-size: 48px; margin-bottom: 12px; }
.done-title { font-size: 20px; font-weight: 700; margin-bottom: 8px; }
.done-sub { font-size: 14px; color: #64748b; }
.portal-link {
  display: inline-block; margin-top: 20px;
  padding: 10px 28px; background: #1a3c5e; color: #fff;
  border-radius: 6px; text-decoration: none; font-size: 14px; font-weight: 600;
}
.portal-link:hover { background: #1e4d7b; }
.brand { padding: 16px 28px; text-align: right;
  font-size: 11px; color: #94a3b8; border-top: 1px solid #f1f5f9; }
"""


def _page_wrap(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — Bull Machines</title>
  <style>{_BASE_CSS}</style>
</head>
<body>
  <div class="card">
    {body}
    <div class="brand">Bull Machines — Manual Production Order System</div>
  </div>
</body>
</html>"""


def _fmt_inr(val: float) -> str:
    return f"₹{val:,.2f}"


def _not_found_page() -> str:
    body = """
    <div class="card-body">
      <div class="done-banner">
        <div class="done-icon">⚠️</div>
        <div class="done-title" style="color:#b45309;">Link Not Found</div>
        <div class="done-sub">This approval link is invalid or has expired.</div>
        <a class="portal-link" href="{APP_URL}">Visit Portal</a>
      </div>
    </div>
    """.replace("{APP_URL}", APP_URL)
    return _page_wrap("Not Found", body)


def _done_section(status: str) -> str:
    if status == "APPROVED":
        return f"""
        <div class="done-banner">
          <div class="done-icon">✅</div>
          <div class="done-title" style="color:#15803d;">Order Approved</div>
          <div class="done-sub">This order has already been approved. No further action is required.</div>
          <a class="portal-link" href="{APP_URL}">Visit Portal</a>
        </div>"""
    return f"""
        <div class="done-banner">
          <div class="done-icon">❌</div>
          <div class="done-title" style="color:#b91c1c;">Order Rejected</div>
          <div class="done-sub">This order has already been rejected. No further action is required.</div>
          <a class="portal-link" href="{APP_URL}">Visit Portal</a>
        </div>"""


# ── Standalone order action page ────────────────────────────────────────────

@router.get("/email/action/{token}", response_class=HTMLResponse)
def email_action_order(token: str):
    order = get_order_by_token(token)
    if not order:
        return HTMLResponse(_not_found_page(), status_code=404)

    user = get_user(order["employee_id"])
    full_name = user["full_name"] if user and user.get("full_name") else order["employee_id"]
    requestor = f"{order['employee_id']} ({full_name})"

    status = order["status"]
    badge = f'<span class="status-badge badge-{status}">{status}</span>'

    remark_html = ""
    if order["remark"]:
        remark_html = f"""
        <div class="remark-box">
          <div class="remark-label">Remark</div>
          {order['remark']}
        </div>"""

    details = f"""
    <div class="detail-grid">
      <span class="detail-label">Requestor</span>
      <span class="detail-value">{requestor}</span>
      <span class="detail-label">Plant</span>
      <span class="detail-value">{order['plant']}</span>
      <span class="detail-label">Part No</span>
      <span class="detail-value">{order['part_no']}</span>
      <span class="detail-label">Quantity</span>
      <span class="detail-value">{order['quantity']:g}</span>
      <span class="detail-label">Unit Price</span>
      <span class="detail-value">{_fmt_inr(order['price'])}</span>
      <span class="detail-label">Total Value</span>
      <span class="detail-value"><strong>{_fmt_inr(order['value'])}</strong></span>
    </div>
    {remark_html}"""

    if status == "PENDING":
        action_html = f"""
        <div class="action-bar">
          <a class="btn-approve" href="/email/approve/{token}">✓ Approve</a>
          <a class="btn-reject"  href="/email/reject/{token}">✗ Reject</a>
        </div>"""
    else:
        action_html = _done_section(status)

    body = f"""
    <div class="card-header">
      <span class="card-title">Production Order</span>
      {badge}
    </div>
    <div class="card-body">
      {details}
      {action_html}
    </div>"""

    return HTMLResponse(_page_wrap("Review Order", body))


# ── Batch order action page ─────────────────────────────────────────────────

@router.get("/email/action/batch/{token}", response_class=HTMLResponse)
def email_action_batch(token: str):
    batch = get_batch_by_token(token)
    if not batch:
        return HTMLResponse(_not_found_page(), status_code=404)

    user = get_user(batch["employee_id"])
    full_name = user["full_name"] if user and user.get("full_name") else batch["employee_id"]
    requestor = f"{batch['employee_id']} ({full_name})"

    items = get_batch_items_by_token(token)
    status = batch["status"]
    badge = f'<span class="status-badge badge-{status}">{status}</span>'

    rows_html = "".join(
        f"<tr>"
        f"<td>{i + 1}</td>"
        f"<td>{it['part_no']}</td>"
        f"<td>{it['plant']}</td>"
        f"<td class='num'>{it['quantity']:g}</td>"
        f"<td class='num'>{_fmt_inr(it['price'])}</td>"
        f"<td class='num'><strong>{_fmt_inr(it['value'])}</strong></td>"
        f"</tr>"
        for i, it in enumerate(items)
    )

    table_html = f"""
    <table>
      <thead>
        <tr>
          <th>#</th><th>Part No</th><th>Plant</th>
          <th class="num">Qty</th><th class="num">Unit Price</th><th class="num">Value</th>
        </tr>
      </thead>
      <tbody>
        {rows_html}
        <tr class="total-row">
          <td colspan="5">Total</td>
          <td class="num">{_fmt_inr(batch['total_value'])}</td>
        </tr>
      </tbody>
    </table>"""

    remark_html = ""
    if batch["remark"]:
        remark_html = f"""
        <div class="remark-box">
          <div class="remark-label">Remark</div>
          {batch['remark']}
        </div>"""

    details = f"""
    <div class="detail-grid">
      <span class="detail-label">Batch ID</span>
      <span class="detail-value"><strong>{batch['batch_id']}</strong></span>
      <span class="detail-label">Requestor</span>
      <span class="detail-value">{requestor}</span>
      <span class="detail-label">Total Value</span>
      <span class="detail-value"><strong>{_fmt_inr(batch['total_value'])}</strong></span>
    </div>
    {remark_html}
    {table_html}"""

    if status == "PENDING":
        action_html = f"""
        <div class="action-bar">
          <a class="btn-approve" href="/email/approve/batch/{token}">✓ Approve All ({len(items)})</a>
          <a class="btn-reject"  href="/email/reject/batch/{token}">✗ Reject All</a>
        </div>"""
    else:
        action_html = _done_section(status)

    body = f"""
    <div class="card-header">
      <span class="card-title">Batch Production Order — {batch['batch_id']}</span>
      {badge}
    </div>
    <div class="card-body">
      {details}
      {action_html}
    </div>"""

    return HTMLResponse(_page_wrap(f"Review Batch {batch['batch_id']}", body))


# ── Approve / Reject handlers — redirect to action page after processing ────

@router.get("/email/approve/{token}", response_class=HTMLResponse)
def email_approve_order(token: str, background_tasks: BackgroundTasks):
    order = get_order_by_token(token)
    if not order:
        return HTMLResponse(_not_found_page(), status_code=404)
    approved_order = approve_order_db(token)
    if approved_order:
        background_tasks.add_task(submit_to_sap, token, approved_order)
    logger.info(f"email_approve: token={token}")
    return RedirectResponse(f"/email/action/{token}", status_code=303)


@router.get("/email/reject/{token}", response_class=HTMLResponse)
def email_reject_order(token: str):
    order = get_order_by_token(token)
    if not order:
        return HTMLResponse(_not_found_page(), status_code=404)
    reject_order(token)
    logger.info(f"email_reject: token={token}")
    return RedirectResponse(f"/email/action/{token}", status_code=303)


@router.get("/email/approve/batch/{token}", response_class=HTMLResponse)
def email_approve_batch(token: str, background_tasks: BackgroundTasks):
    batch = get_batch_by_token(token)
    if not batch:
        return HTMLResponse(_not_found_page(), status_code=404)
    orders = approve_batch_db(token)
    if orders:
        background_tasks.add_task(submit_batch_to_sap, token, orders)
    logger.info(f"email_approve_batch: token={token}")
    return RedirectResponse(f"/email/action/batch/{token}", status_code=303)


@router.get("/email/reject/batch/{token}", response_class=HTMLResponse)
def email_reject_batch(token: str):
    batch = get_batch_by_token(token)
    if not batch:
        return HTMLResponse(_not_found_page(), status_code=404)
    reject_batch(token)
    logger.info(f"email_reject_batch: token={token}")
    return RedirectResponse(f"/email/action/batch/{token}", status_code=303)
