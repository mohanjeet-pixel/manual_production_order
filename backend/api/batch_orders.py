from fastapi import APIRouter, BackgroundTasks, Depends

from backend.schemas.batch import BatchOrderRequest
from backend.schemas.response import StandardResponse
from backend.services.batch_service import create_batch, get_batches, approve_batch, reject_batch
from backend.services.mail_service import send_mail
from backend.dependencies.auth import get_current_user

router = APIRouter(tags=["Batch Orders"])


@router.post("/batches", response_model=StandardResponse)
def create_batch_order(
    request: BatchOrderRequest,
    bg: BackgroundTasks,
    employee_id: str = Depends(get_current_user),
):
    items = [item.model_dump() for item in request.items]
    batch_id, approver, subject, body = create_batch(employee_id, items)
    bg.add_task(send_mail, approver, subject, body)
    return StandardResponse(
        success=True,
        message=f"Batch {batch_id} created successfully",
        data={"batch_id": batch_id},
    )


@router.get("/batches/me")
def my_batches(employee_id: str = Depends(get_current_user)):
    return get_batches(employee_id)


@router.get("/approve/batch/{token}", response_model=StandardResponse)
def approve(token: str):
    approve_batch(token)
    return StandardResponse(success=True, message="Batch approved — all orders updated")


@router.get("/reject/batch/{token}", response_model=StandardResponse)
def reject(token: str):
    reject_batch(token)
    return StandardResponse(success=True, message="Batch rejected — all orders updated")
