from pydantic import BaseModel


class OrderRequest(BaseModel):
    plant: str
    part_no: str
    quantity: float
    remark: str | None = None
