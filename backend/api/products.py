from fastapi import APIRouter, Depends

from backend.repositories.product_repository import get_part_price
from backend.utils.exceptions import PartNotFoundError
from backend.dependencies.auth import get_current_user

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/price/{part_no}")
def get_price(part_no: str, _: str = Depends(get_current_user)):
    price = get_part_price(part_no)
    if price is None:
        raise PartNotFoundError(f"Part '{part_no}' not found")
    return {"part_no": part_no, "price": price}
