from fastapi import APIRouter, Depends, Query

from backend.repositories.plant_repository import get_parts_for_plant
from backend.schemas.response import StandardResponse
from backend.dependencies.auth import get_current_user, CurrentUser

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/parts", response_model=StandardResponse)
def list_parts(
    plant: str = Query(..., description="Plant code — 1000 or 1500"),
    _: CurrentUser = Depends(get_current_user),
):
    """List all parts available for a given plant code."""
    parts = get_parts_for_plant(plant)
    return StandardResponse(success=True, message=f"{len(parts)} parts", data=parts)
