"""Analysis API endpoints."""

import os
import asyncio
from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse

from app.models.schemas import AnalysisRequest, AnalysisResponse, AnalysisStatus
from app.services.db_service import DatabaseService
from app.config import get_settings
from app.utils.logger import get_logger
from app.utils.validators import validate_company_name, validate_industry, validate_job_id

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["analysis"])

# Global service instances (will be initialized in main.py)
db_service: Optional[DatabaseService] = None
orchestrator = None
deck_service = None
llm_service = None


def set_services(db: DatabaseService, orch, deck, llm) -> None:
    """Set service instances."""
    global db_service, orchestrator, deck_service, llm_service
    db_service = db
    orchestrator = orch
    deck_service = deck
    llm_service = llm


@router.post(
    "/clarify",
    summary="Get clarification question",
    description="Get a single clarifying question from LLM before starting analysis"
)
async def get_clarification(request: AnalysisRequest):
    """Get a clarifying question from LLM."""
    try:
        prompt = f"""
        You are a management consulting assistant. User wants an analysis for:
        Company: {request.company_name}
        Industry: {request.industry}
        Strategic Question: {request.strategic_question}
        
        Based on this, ask exactly ONE clarifying question that would help make the analysis more targeted and valuable.
        Keep it brief and professional.
        """
        response = await llm_service.generate(
            prompt=prompt
        )
        
        # If llm_service.generate_json returns a string or dict, adjust accordingly
        # Assuming it returns a string if response_model is None
        question = response if isinstance(response, str) else str(response)
        
        return {"question": question.strip()}
    except Exception as e:
        logger.error("clarification_failed", error=str(e))
        return {"question": "Could you provide more specific details about your primary goal for this analysis?"}


async def run_analysis_background(job_id: str, request_data: Dict):
    """Background task to run complete analysis."""
    try:
        logger.info("background_analysis_starting", job_id=job_id)
        
        # Update status to processing
        await db_service.update_session_status(job_id, "processing", 10)
        
        # Create initial state
        initial_state = {
            "request": request_data,
            "research_data": {},
            "rag_context": [],
            "market_analysis": {},
            "financial_model": {},
            "regulatory_findings": {},
            "synthesis": {},
            "slides": [],
            "errors": [],
            "metadata": {
                "job_id": job_id,
                "created_at": datetime.utcnow().isoformat()
            }
        }
        
        # Execute orchestrator
        logger.info("executing_orchestrator", job_id=job_id)
        final_state = await orchestrator.execute(initial_state)
        
        # Generate outputs (PDF, PPT, JSON)
        logger.info("generating_outputs", job_id=job_id)
        output_paths = await deck_service.generate_all_outputs(
            job_id=job_id,
            slides=final_state.get("slides", []),
            synthesis=final_state.get("synthesis", {}),
            company_name=request_data.get("company_name", "Company")
        )
        
        # Update session with results
        await db_service.update_session_with_results(
            job_id=job_id,
            final_state=final_state,
            output_paths=output_paths
        )
        
        # Mark as completed
        await db_service.update_session_status(job_id, "completed", 100)
        
        logger.info("background_analysis_complete", job_id=job_id)
        
    except Exception as e:
        logger.error("background_analysis_failed", job_id=job_id, error=str(e))
        await db_service.update_session_status(job_id, "failed", 0, error_message=str(e))


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create new analysis job",
    description="Submit a new strategic analysis request and receive a job ID for tracking"
)
async def create_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
) -> AnalysisResponse:
    """Create a new analysis job."""
    # Validate inputs
    if not validate_company_name(request.company_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid company name format"
        )
    
    if not validate_industry(request.industry):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid industry format"
        )
    
    try:
        # Create session data
        session_data = {
            "request": request.model_dump(),
            "metadata": {
                "created_by": "api",
                "version": "1.0.0"
            }
        }
        
        # Save to database
        job_id = await db_service.save_analysis_session(session_data)
        
        logger.info(
            "analysis_job_created",
            job_id=job_id,
            company=request.company_name,
            industry=request.industry
        )
        
        # Add background task
        background_tasks.add_task(
            run_analysis_background,
            job_id,
            request.model_dump()
        )
        
        # Return response
        return AnalysisResponse(
            job_id=job_id,
            status=AnalysisStatus.QUEUED,
            progress=0,
            created_at=datetime.utcnow(),
            completed_at=None,
            result_urls=None
        )
        
    except Exception as e:
        logger.error("create_analysis_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create analysis job"
        )


@router.get(
    "/status/{job_id}",
    response_model=AnalysisResponse,
    summary="Get analysis job status",
    description="Retrieve the current status and progress of an analysis job"
)
async def get_analysis_status(job_id: str) -> AnalysisResponse:
    """Get analysis job status."""
    # Validate job ID format
    if not validate_job_id(job_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job ID format"
        )
    
    try:
        # Retrieve session
        session = await db_service.get_analysis_session(job_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis job {job_id} not found"
            )
        
        # Convert to response model
        return AnalysisResponse(
            job_id=session["job_id"],
            status=AnalysisStatus(session["status"]),
            progress=session["progress"],
            created_at=session["created_at"],
            completed_at=session.get("completed_at"),
            result_urls=session.get("result_urls"),
            error_message=session.get("error_message")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_analysis_status_failed", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analysis status"
        )


@router.get(
    "/results/{job_id}",
    summary="Get analysis results",
    description="Get complete analysis results (JSON)"
)
async def get_analysis_results(job_id: str) -> Dict:
    """Get complete analysis results."""
    if not validate_job_id(job_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job ID format"
        )
    
    try:
        session = await db_service.get_analysis_session(job_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis job {job_id} not found"
            )
        
        if session["status"] != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Analysis not complete: {session['status']}"
            )
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_results_failed", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve results"
        )


@router.get(
    "/download/{job_id}/{format}",
    summary="Download analysis file",
    description="Download PDF, PPTX, or JSON file"
)
async def download_file(job_id: str, format: str):
    """Download generated file."""
    if not validate_job_id(job_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job ID format"
        )
    
    if format not in ["pdf", "pptx", "json"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format must be: pdf, pptx, or json"
        )
    
    try:
        session = await db_service.get_analysis_session(job_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis job {job_id} not found"
            )
        
        if session["status"] != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Analysis not complete: {session['status']}"
            )
        
        output_paths = session.get("output_paths", {})
        file_path = output_paths.get(format)
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {format}"
            )
        
        media_types = {
            "pdf": "application/pdf",
            "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "json": "application/json"
        }
        
        return FileResponse(
            file_path,
            media_type=media_types.get(format, "application/octet-stream"),
            filename=os.path.basename(file_path)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("download_failed", job_id=job_id, format=format, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download file"
        )

