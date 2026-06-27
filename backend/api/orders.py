from fastapi import APIRouter, BackgroundTasks, Depends

from backend.schemas.order import OrderRequest
from backend.schemas.response import StandardResponse
from backend.services.order_service import save_order, get_orders
from backend.services.mail_service import send_mail
from backend.dependencies.auth import get_current_user

router = APIRouter(tags=["Orders"])


@router.post("/orders", response_model=StandardResponse)
def create_order(
    order: OrderRequest,
    bg: BackgroundTasks,
    employee_id: str = Depends(get_current_user),
):
    approver, subject, body = save_order(
        employee_id=employee_id,
        plant=order.plant,
        part_no=order.part_no,
        quantity=order.quantity,
    )
    bg.add_task(send_mail, approver, subject, body)
    return StandardResponse(success=True, message="Order saved successfully")


@router.get("/orders/me")
def my_orders(employee_id: str = Depends(get_current_user)):
    return get_orders(employee_id)
