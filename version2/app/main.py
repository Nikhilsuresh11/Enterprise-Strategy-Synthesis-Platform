"""FastAPI main application for Origin Labs version 2."""

import os
import time
from datetime import datetime
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, List, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.utils.logger import setup_logging, get_logger
from app.models import (
    AnalysisRequest,
    AnalysisResponse,
    QuestionRequest,
    QuestionResponse,
    ChatRequest,
    ChatResponse,
    ChatMessage,
    StartAnalysisRequest
)
from app.services import (
    CacheService,
    LLMService,
    RAGService,
    ExternalDataService,
    PitchDeckService,
    QuestionService,
    PDFReportService
)
from app.agents import (
    EnterpriseIntentAnalyzer,
    CompanyProfilingAgent,
    MarketResearchAgent,
    FinancialAnalysisAgent,
    RiskAssessmentAgent,
    StrategySynthesisAgent,
    ValidationAgent
)
from app.workflows import create_orchestrator, StratagemOrchestrator
from app.models.state import AgentState

# Initialize settings and logging
settings = get_settings()
setup_logging(settings.log_level)
logger = get_logger(__name__)

# Global services
cache_service: CacheService = None
llm_service: LLMService = None
rag_service: RAGService = None
external_service: ExternalDataService = None
pitch_deck_service: PitchDeckService = None
pdf_report_service: PDFReportService = None
question_service: QuestionService = None
orchestrator: StratagemOrchestrator = None

# Chat session storage (in-memory for now)
chat_sessions: Dict[str, List[ChatMessage]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    global cache_service, llm_service, rag_service, external_service, pitch_deck_service, pdf_report_service, question_service, orchestrator
    
    logger.info("application_starting")
    
    try:
        # Initialize services
        logger.info("initializing_services")
        
        cache_service = CacheService(settings.mongodb_uri)
        await cache_service.initialize()
        
        llm_service = LLMService(
            groq_key=settings.groq_api_key,
            openrouter_key=settings.openrouter_api_key,
            cache=cache_service,
            default_model=settings.default_model,
            fast_model=settings.fast_model,
            fallback_model=settings.fallback_model
        )
        
        rag_service = RAGService(
            api_key=settings.pinecone_api_key,
            environment=settings.pinecone_environment,
            index_name=settings.pinecone_index_name,
            cache=cache_service
        )
        
        external_service = ExternalDataService(
            cache=cache_service,
            newsapi_key=settings.newsapi_key
        )
        
        # Initialize pitch deck service
        pitch_deck_service = PitchDeckService()
        
        # Initialize PDF report service
        pdf_report_service = PDFReportService()
        
        # Initialize question service
        question_service = QuestionService(llm_service)
        
        # Initialize agents
        logger.info("initializing_agents")
        
        # Initialize Enterprise Intent Analyzer (MBB-grade)
        intent_agent = EnterpriseIntentAnalyzer(llm_service)
        profile_agent = CompanyProfilingAgent(llm_service, external_service)
        market_agent = MarketResearchAgent(llm_service, rag_service)
        financial_agent = FinancialAnalysisAgent(llm_service, external_service)
        risk_agent = RiskAssessmentAgent(llm_service, rag_service)
        strategy_agent = StrategySynthesisAgent(llm_service)
        validation_agent = ValidationAgent(llm_service)
        
        # Create orchestrator (will add intent_agent later)
        orchestrator = create_orchestrator(
            profile_agent=profile_agent,
            market_agent=market_agent,
            financial_agent=financial_agent,
            risk_agent=risk_agent,
            strategy_agent=strategy_agent,
            validation_agent=validation_agent,
            intent_agent=intent_agent  # Add intent analyzer
        )
        
        logger.info("application_ready")
        
        yield
        
    finally:
        # Cleanup
        logger.info("application_shutting_down")
        
        if cache_service:
            await cache_service.close()
        
        logger.info("application_stopped")


# Create FastAPI application
app = FastAPI(
    title="Origin Labs API",
    description="Enterprise Multi-Agent Strategy Research Platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS - Allow all origins for easier deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (development and production)
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/")
@app.head("/")
async def root():
    """Root endpoint - supports GET and HEAD for health checks."""
    return {
        "name": "Origin Labs",
        "version": "2.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "services": {
            "cache": cache_service is not None,
            "llm": llm_service is not None,
            "rag": rag_service is not None,
            "external": external_service is not None,
            "orchestrator": orchestrator is not None
        }
    }


@app.post("/chat", response_model=ChatResponse)
async def chat_message(request: ChatRequest):
    """
    Handle chat messages in conversational interface.
    
    Args:
        request: Chat message from user
    
    Returns:
        AI response and next action
    """
    import uuid
    from typing import Dict
    
    try:
        logger.info("STEP_1_chat_endpoint_called", session_id=request.session_id or "new")
        
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        
        logger.info(
            "STEP_2_session_identified",
            session_id=session_id,
            message_preview=request.message[:50] if len(request.message) > 50 else request.message,
            company=request.company_name
        )
        
        if session_id not in chat_sessions:
            chat_sessions[session_id] = []
            logger.info("STEP_3_new_session_created", session_id=session_id)
        else:
            logger.info("STEP_3_existing_session", session_id=session_id, message_count=len(chat_sessions[session_id]))
        
        # Add user message to history
        user_msg = ChatMessage(role="user", content=request.message)
        chat_sessions[session_id].append(user_msg)
        logger.info("STEP_4_user_message_added", session_id=session_id)
        
        # Generate AI response using LLM
        chat_history_text = "\n".join([
            f"{'User' if msg.role == 'user' else 'AI'}: {msg.content}"
            for msg in chat_sessions[session_id]
        ])
        
        message_count = len(chat_sessions[session_id])
        logger.info("STEP_5_preparing_prompt", session_id=session_id, message_count=message_count)
        
        # Adjust prompt based on conversation stage
        if message_count <= 2:
            # First exchange - gather basic info
            prompt = f"""You are a helpful strategy analyst assistant. Have a brief conversation to understand the user's needs.

Current conversation:
{chat_history_text}

Guidelines:
1. Be friendly and concise (1-2 sentences)
2. Ask ONE clarifying question to understand their goal
3. Focus on: What do they want to know? (investment, competitive analysis, market entry, etc.)
4. Don't ask multiple questions at once

Respond naturally with ONE follow-up question.
"""
        else:
            # After 1-2 exchanges - suggest analysis
            prompt = f"""You are a helpful strategy analyst assistant. The user has provided enough context.

Current conversation:
{chat_history_text}

Guidelines:
1. Acknowledge their input
2. Suggest starting the analysis
3. Be enthusiastic and concise (1-2 sentences)
4. Example: "Great! I have enough context. Shall I start the comprehensive analysis for [Company]?"

Respond by suggesting to start the analysis.
"""
        
        logger.info("STEP_6_calling_llm", session_id=session_id, message_count=message_count, prompt_length=len(prompt))
        
        try:
            ai_response = await llm_service.generate(
                prompt=prompt,
                task_type="extraction",
                temperature=0.7,
                max_tokens=150
            )
            logger.info("STEP_7_llm_response_received", session_id=session_id, response_length=len(ai_response))
        except Exception as llm_error:
            logger.error("STEP_7_ERROR_llm_failed", session_id=session_id, error=str(llm_error), exc_info=True)
            ai_response = "I apologize, but I'm having trouble processing your message. Could you please try again?"
        
        # Add AI response to history
        ai_msg = ChatMessage(role="assistant", content=ai_response)
        chat_sessions[session_id].append(ai_msg)
        logger.info("STEP_8_ai_response_added", session_id=session_id)
        
        # Determine if ready for analysis
        # After user's initial query + 1-2 follow-ups = 4 messages total (2 user, 2 AI)
        message_count = len(chat_sessions[session_id])
        
        # Trigger analysis after 4 messages (brief conversation)
        # Don't require company_name from request since it may not be extracted yet
        ready_to_analyze = message_count >= 4
        
        action = "ready_for_analysis" if ready_to_analyze else "continue_chat"
        
        logger.info(
            "STEP_9_response_prepared",
            session_id=session_id,
            message_count=message_count,
            ready_to_analyze=ready_to_analyze,
            action=action
        )
        
        response = ChatResponse(
            session_id=session_id,
            message=ai_response,
            action=action,
            ready_to_analyze=ready_to_analyze  # Explicitly set boolean
        )
        
        logger.info("STEP_10_returning_response", session_id=session_id)
        return response
        
    except Exception as e:
        logger.error("STEP_ERROR_chat_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def extract_company_names_from_chat(messages: List[ChatMessage]) -> Dict[str, Any]:
    """
    Extract company names and analysis type from chat conversation.
    
    Looks for:
    - Capitalized words (potential company names)
    - Common company patterns ("X and Y", "X vs Y")
    - Analysis intent (comparison, joint venture, partnership, etc.)
    
    Args:
        messages: List of chat messages
    
    Returns:
        Dict with:
        - companies: List of company names
        - analysis_type: "comparison" | "joint_venture" | "single"
        - company_name: Formatted string for display
    """
    import re
    
    companies = set()
    analysis_type = "single"
    full_text = ""
    
    # Common company suffixes to help identify companies
    company_suffixes = r'(?:Inc\.?|Corp\.?|Ltd\.?|LLC|Co\.?|Group|Motors?|Industries)'
    
    # Exclude common words that are NOT company names
    exclude_words = {
        'I', 'The', 'What', 'How', 'Why', 'When', 'Where', 'Who', 'Which', 
        'Should', 'Could', 'Would', 'Can', 'Will', 'Do', 'Does', 'Is', 'Are', 
        'Am', 'Was', 'Were', 'Been', 'Being', 'Have', 'Has', 'Had', 'May', 
        'Might', 'Must', 'Shall', 'Will', 'Would', 'Company', 'Market', 
        'Industry', 'Business', 'Research', 'Analysis', 'Great', 'Perfect', 
        'Starting', 'Strategic', 'Comprehensive', 'Understanding', 'Considering',
        'Investment', 'Either', 'Looking', 'Gain', 'Competitive', 'Advantage',
        'Primary', 'Goal', 'Current', 'Share', 'Sales', 'Figures', 'Competitor',
        'Landscape', 'Enough', 'Context', 'Shall', 'Start', 'Understand',
        'Their', 'Happy', 'Help', 'That'
    }
    
    for msg in messages:
        if msg.role == "user":
            content = msg.content
            full_text += " " + content.lower()
            
            # Pattern 1: "Company and Company" or "Company vs Company" (case-insensitive)
            multi_company = re.findall(
                r'\b([A-Za-z]+(?:\s+[A-Za-z]+)?)\s+(?:and|vs|versus)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)',
                content,
                re.IGNORECASE
            )
            if multi_company:
                for match in multi_company:
                    # Capitalize and filter out excluded words
                    company1 = match[0].title()
                    company2 = match[1].title()
                    if company1 not in exclude_words and company2 not in exclude_words:
                        companies.add(company1)
                        companies.add(company2)
            
            # Pattern 2: Company with suffix (e.g., "Tesla Inc", "Microsoft Corp") (case-insensitive)
            company_with_suffix = re.findall(
                rf'\b([A-Za-z]+(?:\s+[A-Za-z]+)?)\s+{company_suffixes}\b',
                content,
                re.IGNORECASE
            )
            if company_with_suffix:
                companies.update([c.title() for c in company_with_suffix])
            
            # Pattern 3: Capitalized words (2-3 words max, likely company names)
            # Only add if not in exclude list
            capitalized = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b', content)
            for word in capitalized:
                # Check if word or any part of it is in exclude list
                word_parts = word.split()
                if not any(part in exclude_words for part in word_parts) and len(word) > 2:
                    companies.add(word)
    
    # Detect analysis type from keywords
    if len(companies) > 1:
        # Check for joint venture/partnership keywords
        jv_keywords = ['joint venture', 'partnership', 'collaborate', 'collaboration', 'merge', 'merger', 'acquisition', 'partner', 'alliance', 'combine', 'together']
        if any(keyword in full_text for keyword in jv_keywords):
            analysis_type = "joint_venture"
        else:
            # Check for comparison keywords
            comparison_keywords = ['compare', 'comparison', 'versus', 'vs', 'better', 'difference', 'which', 'competitive']
            if any(keyword in full_text for keyword in comparison_keywords):
                analysis_type = "comparison"
            else:
                # Default to comparison for multi-company
                analysis_type = "comparison"
    
    companies_list = sorted(list(companies))[:3]  # Limit to 3 companies
    
    if not companies_list:
        return {
            "companies": ["Unknown Company"],
            "analysis_type": "single",
            "company_name": "Unknown Company"
        }
    
    # Format company name for display
    if len(companies_list) == 1:
        company_name = companies_list[0]
    elif analysis_type == "joint_venture":
        company_name = " + ".join(companies_list)  # Use + for joint ventures
    else:
        company_name = " vs ".join(companies_list)  # Use vs for comparisons
    
    return {
        "companies": companies_list,
        "analysis_type": analysis_type,
        "company_name": company_name
    }


@app.post("/chat/analyze", response_model=AnalysisResponse)
async def analyze_from_chat(request: StartAnalysisRequest):
    """
    Start analysis from chat conversation.
    User has confirmed they want to proceed with analysis.
    
    Args:
        request: Chat history and analysis parameters
    
    Returns:
        Analysis response with results
    """
    try:
        # Extract company names and analysis type from chat if not provided
        if not request.company_name or request.company_name == "Company":
            extraction_result = extract_company_names_from_chat(request.chat_history)
            company_name = extraction_result["company_name"]
            companies = extraction_result["companies"]
            analysis_type = extraction_result["analysis_type"]
            
            logger.info(
                "extracted_company_from_chat",
                extracted_name=company_name,
                companies=companies,
                analysis_type=analysis_type,
                original_name=request.company_name
            )
        else:
            company_name = request.company_name
            companies = [company_name]
            analysis_type = "single"
        
        logger.info(
            "chat_analysis_request_received",
            session_id=request.session_id,
            company=company_name,
            companies=companies,
            analysis_type=analysis_type,
            industry=request.industry,
            chat_messages=len(request.chat_history),
            output_formats=request.output_format
        )
        
        # Create initial state with chat history and company info
        initial_state: AgentState = {
            "request": {
                "company_name": company_name,  # Use extracted company name
                "companies": companies,  # List of companies
                "analysis_type": analysis_type,  # comparison | joint_venture | single
                "industry": request.industry,
                "question": "Analysis based on chat conversation",
                "include_mna": False
            },
            "chat_history": [msg.dict() for msg in request.chat_history],
            "errors": [],
            "metadata": {}
        }
        
        logger.info("starting_orchestrator_execution", company=company_name)
        
        # Execute workflow (Intent Analyzer will run first)
        final_state = await orchestrator.execute(initial_state)
        
        logger.info(
            "orchestrator_completed",
            company=company_name,
            has_errors=len(final_state.get("errors", [])) > 0
        )
        
        # Generate outputs
        output_urls = []
        
        # Generate PDF report
        if "pdf" in request.output_format or "json" in request.output_format:
            try:
                logger.info("generating_pdf_report", company=company_name)
                
                output_dir = "output/reports"
                os.makedirs(output_dir, exist_ok=True)
                
                pdf_filename = f"{request.company_name.replace(' ', '_')}_{int(time.time())}.pdf"
                pdf_path = os.path.join(output_dir, pdf_filename)
                
                await pdf_report_service.generate_report(
                    company_name=request.company_name,
                    analysis_data=final_state,
                    output_path=pdf_path
                )
                
                output_urls.append(pdf_path)
                logger.info("pdf_report_generated", path=pdf_path)
                
            except Exception as e:
                logger.error("pdf_report_generation_failed", error=str(e), exc_info=True)
        
        # Generate pitch deck
        if "ppt" in request.output_format:
            try:
                logger.info("generating_pitch_deck", company=company_name)
                
                output_dir = "output/decks"
                os.makedirs(output_dir, exist_ok=True)
                
                deck_filename = f"{request.company_name.replace(' ', '_')}_{int(time.time())}.pptx"
                deck_path = os.path.join(output_dir, deck_filename)
                
                await pitch_deck_service.generate_deck(
                    company_name=request.company_name,
                    analysis_data=final_state,
                    output_path=deck_path
                )
                
                output_urls.append(deck_path)
                logger.info("pitch_deck_generated", path=deck_path)
                
            except Exception as e:
                logger.error("pitch_deck_generation_failed", error=str(e), exc_info=True)
        
        # Build response
        response = AnalysisResponse(
            analysis_id=f"analysis_{request.company_name}_{int(time.time())}",
            company_name=request.company_name,
            status="completed" if not final_state.get("errors") else "completed_with_errors",
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            summary=final_state.get("strategy_synthesis", {}).get("executive_summary", ""),
            output_urls=output_urls,
            execution_time=final_state.get("metadata", {}).get("total_execution_time", 0),
            errors=final_state.get("errors", [])
        )
        
        # Clean up chat session
        if request.session_id in chat_sessions:
            del chat_sessions[request.session_id]
            logger.info("chat_session_cleaned_up", session_id=request.session_id)
        
        logger.info(
            "chat_analysis_completed",
            company=request.company_name,
            status=response.status,
            execution_time=response.execution_time
        )
        
        return response
        
    except Exception as e:
        logger.error("chat_analysis_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/questions", response_model=QuestionResponse)
async def get_clarifying_questions(request: QuestionRequest):
    """
    Generate clarifying questions before analysis.
    
    Args:
        request: Question request with company name and initial question
    
    Returns:
        2-3 clarifying questions with multiple choice options
    """
    try:
        logger.info(
            "questions_request_received",
            company=request.company_name,
            question=request.question[:50]
        )
        
        # Generate questions
        questions = await question_service.generate_questions(
            company_name=request.company_name,
            industry=request.industry or "Unknown",
            question=request.question
        )
        
        response = QuestionResponse(questions=questions)
        
        logger.info(
            "questions_generated",
            company=request.company_name,
            count=len(questions)
        )
        
        return response
        
    except Exception as e:
        logger.error("questions_generation_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_company(request: AnalysisRequest):
    """
    Analyze a company and generate strategic recommendations.
    
    Args:
        request: Analysis request with company name and question
    
    Returns:
        Analysis response with results and optional pitch deck
    """
    try:
        logger.info(
            "analysis_request_received",
            company=request.company_name,
            question=request.question[:50]
        )
        
        # Create initial state
        initial_state: AgentState = {
            "request": {
                "company_name": request.company_name,
                "industry": request.industry,
                "question": request.question,
                "include_mna": request.include_mna
            },
            "errors": [],
            "metadata": {}
        }
        
        # Execute workflow
        final_state = await orchestrator.execute(initial_state)
        
        # Generate pitch deck if requested
        output_urls = None
        if "ppt" in request.output_format:
            try:
                # Create output directory if it doesn't exist
                output_dir = "output/decks"
                os.makedirs(output_dir, exist_ok=True)
                
                # Generate deck
                deck_filename = f"{request.company_name.replace(' ', '_')}_{int(time.time())}.pptx"
                deck_path = os.path.join(output_dir, deck_filename)
                
                await pitch_deck_service.generate_deck(
                    company_name=request.company_name,
                    analysis_data=final_state,
                    output_path=deck_path
                )
                
                output_urls = [deck_path]
                
                logger.info("pitch_deck_generated", path=deck_path)
                
            except Exception as e:
                logger.error("pitch_deck_generation_failed", error=str(e))
                # Continue even if deck generation fails
        
        # Build response
        response = AnalysisResponse(
            analysis_id=f"analysis_{request.company_name}_{int(time.time())}",
            company_name=request.company_name,
            status="completed" if not final_state.get("errors") else "completed_with_errors",
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            summary=final_state.get("strategy_synthesis", {}).get("executive_summary", ""),
            output_urls=output_urls,
            execution_time=final_state.get("metadata", {}).get("total_execution_time", 0),
            errors=final_state.get("errors", [])
        )
        
        logger.info(
            "analysis_completed",
            company=request.company_name,
            status=response.status,
            execution_time=response.execution_time,
            deck_generated=output_urls is not None
        )
        
        return response
        
    except Exception as e:
        logger.error("analysis_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download/{file_path:path}")
async def download_file(file_path: str):
    """
    Download generated files (pitch decks, reports, etc.)
    
    Args:
        file_path: Relative path to the file (e.g., "output/decks/Tesla_123.pptx")
    
    Returns:
        File download response
    """
    from fastapi.responses import FileResponse
    import os
    
    try:
        # Construct full path
        full_path = os.path.join(os.getcwd(), file_path)
        
        # Security check: ensure file is within allowed directories
        if not full_path.startswith(os.path.join(os.getcwd(), "output")):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Check if file exists
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get filename for download
        filename = os.path.basename(full_path)
        
        logger.info("file_download_requested", path=file_path)
        
        return FileResponse(
            path=full_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("file_download_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    import time
    from datetime import datetime
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower()
    )
