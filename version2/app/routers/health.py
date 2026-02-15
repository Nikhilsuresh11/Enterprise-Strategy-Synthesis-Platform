"""Health and root endpoints."""

from fastapi import APIRouter, Request

router = APIRouter(tags=["Health"])


@router.get("/")
@router.head("/")
async def root():
    return {
        "name": "Origin Labs",
        "version": "2.0.0",
        "status": "running"
    }


@router.get("/health")
async def health_check(request: Request):
    state = request.app.state
    return {
        "status": "healthy",
        "services": {
            "cache": getattr(state, "cache_service", None) is not None,
            "llm": getattr(state, "llm_service", None) is not None,
            "rag": getattr(state, "rag_service", None) is not None,
            "external": getattr(state, "external_service", None) is not None,
            "orchestrator": getattr(state, "orchestrator", None) is not None,
            "database": getattr(state, "db_service", None) is not None,
        }
    }
