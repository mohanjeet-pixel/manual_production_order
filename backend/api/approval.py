from fastapi import APIRouter

from backend.schemas.response import StandardResponse
from backend.services.approval_service import approve_order, reject_order

router = APIRouter(tags=["Approval"])


@router.get("/approve/{token}", response_model=StandardResponse)
def approve(token: str):
    approve_order(token)
    return StandardResponse(success=True, message="Order approved successfully")


@router.get("/reject/{token}", response_model=StandardResponse)
def reject(token: str):
    reject_order(token)
    return StandardResponse(success=True, message="Order rejected successfully")
