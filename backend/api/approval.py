from fastapi import APIRouter, BackgroundTasks

from backend.schemas.response import StandardResponse
from backend.services.approval_service import approve_order_db, submit_to_sap, reject_order

router = APIRouter(tags=["Approval"])


@router.get("/approve/{token}", response_model=StandardResponse)
def approve(token: str, background_tasks: BackgroundTasks):
    order = approve_order_db(token)
    background_tasks.add_task(submit_to_sap, token, order)
    return StandardResponse(
        success=True,
        message="Order approved — SAP submission running in background",
        data={"order_approved": True},
    )


@router.get("/reject/{token}", response_model=StandardResponse)
def reject(token: str):
    reject_order(token)
    return StandardResponse(success=True, message="Order rejected successfully")
