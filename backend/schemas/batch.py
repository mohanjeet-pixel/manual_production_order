from pydantic import BaseModel


class BatchItem(BaseModel):
    plant: str
    part_no: str
    quantity: float


class BatchOrderRequest(BaseModel):
    items: list[BatchItem]
