"""FastAPI main application for Origin Labs version 2."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.config import get_settings
from app.utils.logger import setup_logging, get_logger
from app.services import (
    CacheService,
    LLMService,
    RAGService,
    ExternalDataService,
    PitchDeckService,
    QuestionService,
    PDFReportService,
    AuthService,
    DatabaseService,
)
from app.agents import (
    EnterpriseIntentAnalyzer,
    CompanyProfilingAgent,
    MarketResearchAgent,
    FinancialAnalysisAgent,
    RiskAssessmentAgent,
    StrategySynthesisAgent,
    ValidationAgent,
)
from app.workflows import create_orchestrator

# Routers
from app.routers.health import router as health_router
from app.routers.auth import router as auth_router
from app.routers.chat import router as chat_router
from app.routers.analysis import router as analysis_router
from app.routers.documents import router as documents_router

# Initialize settings and logging
settings = get_settings()
setup_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Initialize and clean up all services."""
    
    logger.info("application_starting")
    
    try:
        # Core services
        cache_service = CacheService(settings.mongodb_uri)
        await cache_service.initialize()
        
        db_service = DatabaseService(settings.mongodb_uri)
        await db_service.initialize()
        
        auth_service = AuthService(
            secret_key=settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
            expiration_minutes=settings.jwt_expiration_minutes,
        )
        
        llm_service = LLMService(
            groq_key=settings.groq_api_key,
            openrouter_key=settings.openrouter_api_key,
            cache=cache_service,
            default_model=settings.default_model,
            fast_model=settings.fast_model,
            fallback_model=settings.fallback_model,
        )
        
        rag_service = RAGService(
            api_key=settings.pinecone_api_key,
            environment=settings.pinecone_environment,
            index_name=settings.pinecone_index_name,
            cache=cache_service,
        )
        
        external_service = ExternalDataService(
            cache=cache_service,
            newsapi_key=settings.newsapi_key,
        )
        
        pitch_deck_service = PitchDeckService()
        pdf_report_service = PDFReportService()
        question_service = QuestionService(llm_service)
        
        # Agents
        intent_agent = EnterpriseIntentAnalyzer(llm_service)
        profile_agent = CompanyProfilingAgent(llm_service, external_service)
        market_agent = MarketResearchAgent(llm_service, rag_service)
        financial_agent = FinancialAnalysisAgent(llm_service, external_service)
        risk_agent = RiskAssessmentAgent(llm_service, rag_service)
        strategy_agent = StrategySynthesisAgent(llm_service)
        validation_agent = ValidationAgent(llm_service)
        
        orchestrator = create_orchestrator(
            profile_agent=profile_agent,
            market_agent=market_agent,
            financial_agent=financial_agent,
            risk_agent=risk_agent,
            strategy_agent=strategy_agent,
            validation_agent=validation_agent,
            intent_agent=intent_agent,
        )
        
        # Store services on app.state for router access
        app.state.cache_service = cache_service
        app.state.db_service = db_service
        app.state.auth_service = auth_service
        app.state.llm_service = llm_service
        app.state.rag_service = rag_service
        app.state.external_service = external_service
        app.state.pitch_deck_service = pitch_deck_service
        app.state.pdf_report_service = pdf_report_service
        app.state.question_service = question_service
        app.state.orchestrator = orchestrator
        
        logger.info("application_ready")
        yield
        
    finally:
        logger.info("application_shutting_down")
        if hasattr(app.state, "cache_service") and app.state.cache_service:
            await app.state.cache_service.close()
        if hasattr(app.state, "db_service") and app.state.db_service:
            await app.state.db_service.close()
        logger.info("application_stopped")


# ==================== App Setup ====================

app = FastAPI(
    title="Origin Labs API",
    description="Enterprise Multi-Agent Strategy Research Platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS — use configured origins instead of wildcard
origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(analysis_router)
app.include_router(documents_router)


# ==================== File Download (kept inline — simple) ====================

@app.get("/download/{file_path:path}")
async def download_file(file_path: str):
    """Download generated report files."""
    import os
    
    full_path = os.path.join(os.getcwd(), file_path)
    
    if not full_path.startswith(os.path.join(os.getcwd(), "output")):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not os.path.exists(full_path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="File not found")
    
    filename = os.path.basename(full_path)
    return FileResponse(
        path=full_path,
        filename=filename,
        media_type="application/octet-stream",
    )


# ==================== Entry Point ====================

if __name__ == "__main__":
    import os
    import uvicorn

    # Render (and most cloud platforms) inject PORT as an env var.
    # pydantic-settings reads it automatically via the `port` field,
    # but we also do an explicit fallback here for safety.
    port = int(os.environ.get("PORT", settings.port))
    is_dev = settings.app_env == "development"

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=port,
        reload=is_dev,          # Never reload in production
        log_level=settings.log_level.lower(),
    )
