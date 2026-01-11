"""Stratagem AI - FastAPI Application Entry Point."""

import psutil
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routers import analysis
from app.routers import auth
from app.routers.analysis import router as analysis_router
from app.routers.auth import router as auth_router
from app.services.db_service import DatabaseService
from app.services.rag_service import RAGService
from app.services.llm_service import LLMService
from app.services.external_apis import ExternalDataService
from app.services.deck_service import DeckGenerationService
from app.agents.researcher import ResearchAgent
from app.agents.analyst import AnalystAgent
from app.agents.regulatory import RegulatoryAgent
from app.agents.synthesizer import SynthesizerAgent
from app.workflows.orchestrator import StratagemOrchestrator
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Memory logging helper
def log_memory(stage: str):
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    mem_mb = mem_info.rss / 1024 / 1024
    logger.info(f"💾 MEMORY [{stage}]: {mem_mb:.2f} MB")
    print(f"💾 MEMORY [{stage}]: {mem_mb:.2f} MB")

# Global services
db_service: DatabaseService = None
orchestrator: StratagemOrchestrator = None
rag_service: RAGService = None # Added to make it accessible for set_services
llm_service: LLMService = None # Added to make it accessible for set_services
external_service: ExternalDataService = None # Added to make it accessible for set_services
deck_service: DeckGenerationService = None # Added to make it accessible for set_services


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    global db_service, orchestrator, rag_service, llm_service, external_service, deck_service
    
    log_memory("APP_START")
    logger.info("application_starting", version="1.0.0")
    
    try:
        # Initialize core services
        logger.info("initializing_services")
        
        db_service = DatabaseService(
            mongodb_uri=settings.mongodb_uri,
            db_name=settings.mongodb_db_name
        )
        await db_service.connect()
        log_memory("AFTER_DB")
        
        # Initialize RAG service (lazy - may fail if PyTorch not available)
        rag_service = None
        if settings.enable_rag:
            try:
                logger.info("initializing_rag_service")
                rag_service = RAGService(
                    api_key=settings.pinecone_api_key,
                    environment=settings.pinecone_environment,
                    index_name=settings.pinecone_index_name
                )
                await rag_service.connect()
                log_memory("AFTER_RAG")
                logger.info("rag_service_initialized")
            except Exception as rag_error:
                logger.warning("rag_service_initialization_failed", error=str(rag_error))
                logger.info("continuing_without_rag_service")
        else:
            logger.info("rag_service_disabled_by_config")
        
        llm_service = LLMService(
            groq_api_key=settings.groq_api_key,
            groq_model=settings.groq_model,
            groq_fast_model=settings.groq_fast_model,
            openrouter_api_key=settings.openrouter_api_key,
            openrouter_model=settings.openrouter_model,
            openrouter_site_url=settings.openrouter_site_url,
            openrouter_site_name=settings.openrouter_site_name,
            max_retries=settings.llm_max_retries,
            retry_delay=settings.llm_retry_delay,
            rate_limit_delay=settings.llm_rate_limit_delay
        )
        
        external_service = ExternalDataService(newsapi_key=settings.newsapi_key)
        
        deck_service = DeckGenerationService(output_dir="outputs")
        
        # Initialize agents
        logger.info("initializing_agents")
        
        research_agent = ResearchAgent(rag_service, llm_service, db_service, external_service)
        analyst_agent = AnalystAgent(llm_service, db_service)
        regulatory_agent = RegulatoryAgent(llm_service, rag_service, db_service)
        synthesizer_agent = SynthesizerAgent(llm_service, db_service)
        
        # Initialize orchestrator
        logger.info("initializing_orchestrator")
        
        orchestrator = StratagemOrchestrator(
            research_agent,
            analyst_agent,
            regulatory_agent,
            synthesizer_agent
        )
        
        # Set services for routers (db, orchestrator, deck_service, llm_service)
        analysis.set_services(db_service, orchestrator, deck_service, llm_service)
        auth.set_services(db_service)
        
        log_memory("AFTER_ALL_AGENTS")
        logger.info("application_started")
        
    except Exception as e:
        logger.error("application_startup_failed", error=str(e), exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("application_shutting_down")
    
    if db_service:
        await db_service.disconnect()
    
    logger.info("application_shutdown_complete")



# Create FastAPI application
app = FastAPI(
    title="Stratagem AI",
    description="Enterprise Multi-Agent Management Consulting System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analysis_router)
app.include_router(auth_router)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.api_route(
    "/health",
    methods=["GET", "HEAD"],
    tags=["health"],
    summary="Health check endpoint",
    description="Check if the API is running and database is connected"
)
async def health_check() -> JSONResponse:
    """
    Health check endpoint.
    
    Returns:
        JSON response with health status
    """
    health_status = {
        "status": "healthy",
        "version": "1.0.0",
        "service": "stratagem-ai"
    }
    
    # Check database connection
    if db_service and db_service._initialized:
        health_status["database"] = "connected"
    else:
        health_status["database"] = "disconnected"
        health_status["status"] = "degraded"
    
    logger.debug("health_check", status=health_status["status"])
    
    return JSONResponse(content=health_status)


@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    """Serve main application page."""
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "name": "Stratagem AI",
        "version": "1.0.0",
        "description": "Enterprise Multi-Agent Management Consulting System (Static frontend missing)",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/login")
async def login_page():
    """Serve login page."""
    login_path = os.path.join(os.path.dirname(__file__), "static", "login.html")
    if os.path.exists(login_path):
        return FileResponse(login_path)
    return {"error": "Login page not found"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower()
    )
