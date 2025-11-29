from fastapi import APIRouter

from app.api.v1.endpoints import (
    ab,
    auth,
    events,
    explain,
    interactions,
    recommendations,
    stats,
)

api_v1_router = APIRouter(prefix="/api/v1")

# Регистрируем подроутеры
api_v1_router.include_router(auth.router)
api_v1_router.include_router(interactions.router)
api_v1_router.include_router(recommendations.router)
api_v1_router.include_router(ab.router)
api_v1_router.include_router(events.router)
api_v1_router.include_router(explain.router)
api_v1_router.include_router(stats.router)


@api_v1_router.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok"}
