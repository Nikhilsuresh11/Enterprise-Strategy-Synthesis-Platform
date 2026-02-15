"""Analysis router — direct analysis and question generation endpoints."""

import os
import time
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, Depends

from app.models.schemas import AnalysisRequest, AnalysisResponse, QuestionRequest, QuestionResponse
from app.models.state import AgentState
from app.services.auth_service import get_current_user_id
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/analyze", tags=["Analysis"])


@router.post("/questions", response_model=QuestionResponse)
async def get_clarifying_questions(
    request: Request,
    body: QuestionRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Generate clarifying questions for an analysis."""
    
    question_service = request.app.state.question_service
    
    try:
        questions = await question_service.generate_questions(
            company_name=body.company_name,
            industry=body.industry or "Unknown",
            question=body.question
        )
        
        return QuestionResponse(questions=questions)
        
    except Exception as e:
        logger.error("questions_generation_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=AnalysisResponse)
async def analyze_company(
    request: Request,
    body: AnalysisRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Run a direct company analysis (non-chat flow)."""
    
    orchestrator = request.app.state.orchestrator
    pitch_deck_service = request.app.state.pitch_deck_service
    pdf_report_service = request.app.state.pdf_report_service
    db = request.app.state.db_service
    
    try:
        # Create initial state
        initial_state: AgentState = {
            "request": {
                "company_name": body.company_name,
                "industry": body.industry,
                "question": body.question,
                "include_mna": body.include_mna
            },
            "errors": [],
            "metadata": {}
        }
        
        # Execute workflow
        final_state = await orchestrator.execute(initial_state)
        
        # Generate outputs
        output_urls = []
        
        if "pdf" in body.output_format:
            try:
                output_dir = "output/reports"
                os.makedirs(output_dir, exist_ok=True)
                pdf_filename = f"{body.company_name.replace(' ', '_')}_{int(time.time())}.pdf"
                pdf_path = os.path.join(output_dir, pdf_filename)
                await pdf_report_service.generate_report(
                    company_name=body.company_name,
                    analysis_data=final_state,
                    output_path=pdf_path
                )
                output_urls.append(pdf_path)
            except Exception as e:
                logger.error("pdf_generation_failed", error=str(e))
        
        if "ppt" in body.output_format:
            try:
                output_dir = "output/decks"
                os.makedirs(output_dir, exist_ok=True)
                deck_filename = f"{body.company_name.replace(' ', '_')}_{int(time.time())}.pptx"
                deck_path = os.path.join(output_dir, deck_filename)
                await pitch_deck_service.generate_deck(
                    company_name=body.company_name,
                    analysis_data=final_state,
                    output_path=deck_path
                )
                output_urls.append(deck_path)
            except Exception as e:
                logger.error("deck_generation_failed", error=str(e))
        
        # Build response
        analysis_id = f"analysis_{body.company_name}_{int(time.time())}"
        response = AnalysisResponse(
            analysis_id=analysis_id,
            company_name=body.company_name,
            status="completed" if not final_state.get("errors") else "completed_with_errors",
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            summary=final_state.get("strategy_synthesis", {}).get("executive_summary", ""),
            output_urls=output_urls or None,
            execution_time=final_state.get("metadata", {}).get("total_execution_time", 0),
            errors=final_state.get("errors", [])
        )
        
        # Save analysis to DB
        await db.save_analysis(user_id, {
            "_id": analysis_id,
            "company_name": body.company_name,
            "status": response.status,
            "summary": response.summary,
            "output_urls": output_urls,
            "execution_time": response.execution_time,
            "errors": response.errors,
        })
        
        return response
        
    except Exception as e:
        logger.error("analysis_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=list)
async def list_analyses(
    request: Request,
    user_id: str = Depends(get_current_user_id)
):
    """List past analyses for the current user."""
    
    db = request.app.state.db_service
    analyses = await db.list_user_analyses(user_id)
    
    # Format for response
    result = []
    for a in analyses:
        result.append({
            "id": a["_id"],
            "company_name": a.get("company_name", ""),
            "status": a.get("status", ""),
            "summary": a.get("summary", "")[:200],
            "execution_time": a.get("execution_time"),
            "created_at": a.get("created_at", datetime.utcnow()).isoformat(),
            "output_urls": a.get("output_urls", []),
        })
    
    return result
