from fastapi import APIRouter
from fastapi_foundation.models.api_response import ApiResponse
from pydantic import BaseModel


router = APIRouter()


class HealthCheckResponse(BaseModel):
    status: str

@router.get("/health")
async def health_check():
    health_check = HealthCheckResponse(
        status="healthy"
    )
    return ApiResponse[HealthCheckResponse](
        status="success",
        code=200,
        data=health_check
    )