from fastapi import APIRouter, BackgroundTasks, Depends

from backend.schemas.batch import BatchOrderRequest
from backend.schemas.response import StandardResponse
from backend.services.batch_service import (
    create_batch, get_batches,
    approve_batch_db, submit_batch_to_sap,
    reject_batch,
)
from backend.services.mail_service import send_mail
from backend.dependencies.auth import require_operator, CurrentUser

router = APIRouter(tags=["Batch Orders"])


@router.post("/batches", response_model=StandardResponse)
def create_batch_order(
    request: BatchOrderRequest,
    bg: BackgroundTasks,
    user: CurrentUser = Depends(require_operator),
):
    items = [item.model_dump() for item in request.items]
    batch_id, approver, subject, body = create_batch(user.employee_id, items)
    bg.add_task(send_mail, approver, subject, body)
    return StandardResponse(
        success=True,
        message=f"Batch {batch_id} created successfully",
        data={"batch_id": batch_id},
    )


@router.get("/batches/me", response_model=StandardResponse)
def my_batches(user: CurrentUser = Depends(require_operator)):
    data = get_batches(user.employee_id)
    return StandardResponse(success=True, message=f"{len(data)} batches", data=data)


@router.get("/approve/batch/{token}", response_model=StandardResponse)
def approve(token: str, background_tasks: BackgroundTasks):
    orders = approve_batch_db(token)
    background_tasks.add_task(submit_batch_to_sap, token, orders)
    return StandardResponse(
        success=True,
        message=f"Batch approved — SAP submission running in background for {len(orders)} orders",
        data={"order_count": len(orders)},
    )


@router.get("/reject/batch/{token}", response_model=StandardResponse)
def reject(token: str):
    reject_batch(token)
    return StandardResponse(success=True, message="Batch rejected — all orders updated")
