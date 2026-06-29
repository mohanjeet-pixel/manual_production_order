from fastapi import APIRouter, BackgroundTasks, Depends, Query

from backend.schemas.response import StandardResponse
from backend.services.management_service import approval_queue, approval_history, re_approve_db, batch_queue
from backend.services.approval_service import submit_to_sap
from backend.dependencies.auth import require_manager, CurrentUser

router = APIRouter(prefix="/management", tags=["Management"])


@router.get("/batches/queue", response_model=StandardResponse)
def get_batch_queue_endpoint(user: CurrentUser = Depends(require_manager)):
    """Pending batch orders waiting for this manager's approval."""
    batches = batch_queue(user.employee_id)
    return StandardResponse(success=True, message=f"{len(batches)} pending batches", data=batches)


@router.get("/queue", response_model=StandardResponse)
def get_queue(user: CurrentUser = Depends(require_manager)):
    """Pending orders waiting for this manager's approval."""
    orders = approval_queue(user.employee_id)
    return StandardResponse(success=True, message=f"{len(orders)} pending orders", data=orders)


@router.get("/history", response_model=StandardResponse)
def get_history(
    status: str | None = Query(None, description="Filter: PENDING, APPROVED, REJECTED"),
    user: CurrentUser = Depends(require_manager),
):
    """All orders routed to this manager, optionally filtered by status."""
    orders = approval_history(user.employee_id, status_filter=status)
    return StandardResponse(success=True, message=f"{len(orders)} orders", data=orders)


@router.post("/orders/{token}/re-approve", response_model=StandardResponse)
def reapprove(token: str, background_tasks: BackgroundTasks,
              user: CurrentUser = Depends(require_manager)):
    """Re-approve a wrongly rejected order. Allowed only once per order."""
    order = re_approve_db(token, user.employee_id)
    background_tasks.add_task(submit_to_sap, token, order)
    return StandardResponse(
        success=True,
        message="Order re-approved — SAP submission running in background",
        data={"order_approved": True},
    )
