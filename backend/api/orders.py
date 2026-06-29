from fastapi import APIRouter, BackgroundTasks, Depends

from backend.schemas.order import OrderRequest
from backend.schemas.response import StandardResponse
from backend.services.order_service import save_order, get_orders
from backend.services.mail_service import send_mail
from backend.dependencies.auth import require_operator, CurrentUser

router = APIRouter(tags=["Orders"])


@router.post("/orders", response_model=StandardResponse)
def create_order(
    order: OrderRequest,
    bg: BackgroundTasks,
    user: CurrentUser = Depends(require_operator),
):
    approver, subject, body = save_order(
        employee_id=user.employee_id,
        plant=order.plant,
        part_no=order.part_no,
        quantity=order.quantity,
    )
    bg.add_task(send_mail, approver, subject, body)
    return StandardResponse(success=True, message="Order saved successfully")


@router.get("/orders/me")
def my_orders(user: CurrentUser = Depends(require_operator)):
    return get_orders(user.employee_id)
