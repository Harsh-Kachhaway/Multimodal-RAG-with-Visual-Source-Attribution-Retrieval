from fastapi import APIRouter, Depends
from app.core.config import settings
from app.models.schemas import HealthResponse
from app.api.dependencies import get_database_manager, VectorDatabaseManager

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def check_system_health(
    database: VectorDatabaseManager = Depends(get_database_manager)
):
    is_connected = await database.is_healthy()
    return HealthResponse(
        status="healthy" if is_connected else "degraded",
        app_name=settings.app_name,
        database_connected=is_connected,
        model_name=settings.llm_model,
        environment=settings.app_environment
    )

