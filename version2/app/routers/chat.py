"""Chat router with MongoDB persistence and session management."""

import uuid
import asyncio
import json
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field

from app.models.chat_schemas import ChatMessage, ChatRequest, ChatResponse, StartAnalysisRequest
from app.models.schemas import AnalysisResponse
from app.services.auth_service import get_current_user_id
from app.models.state import AgentState
from app.utils.logger import get_logger

import os
import time
from datetime import datetime

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

# In-memory cache for comparison data (keyed by comparison_id)
_comparison_cache: Dict[str, Dict[str, Any]] = {}


# ==================== Request/Response Models ====================

class SessionTitleUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


class SessionListItem(BaseModel):
    id: str
    title: str
    company_name: Optional[str] = None
    preview: str = ""
    created_at: str
    updated_at: str


# ==================== Chat Endpoints ====================


@router.post("", response_model=ChatResponse)
async def chat_message(
    request: Request,
    body: ChatRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Send a chat message. Creates a session if none exists."""
    
    db = request.app.state.db_service
    llm = request.app.state.llm_service
    
    try:
        # Get or create session
        session_id = body.session_id
        session = None
        
        if session_id:
            session = await db.get_chat_session(session_id, user_id)
        
        if not session:
            title = body.message[:60] + ("..." if len(body.message) > 60 else "")
            session = await db.create_chat_session(user_id, title)
            session_id = session["_id"]
        
        # Add user message to DB
        await db.add_message_to_session(session_id, user_id, "user", body.message)
        
        # Get updated session
        session = await db.get_chat_session(session_id, user_id)
        messages = session.get("messages", [])
        user_messages_count = sum(1 for m in messages if m["role"] == "user")
        
        # ── Extract companies from ALL user messages so far ──
        from app.routers._chat_utils import extract_company_names_from_chat
        from app.models.chat_schemas import ChatMessage as CM
        
        chat_msgs = [CM(role=m["role"], content=m["content"]) for m in messages]
        extraction = await extract_company_names_from_chat(chat_msgs, llm)
        
        company_name = extraction["company_name"]
        companies = extraction["companies"]
        analysis_type = extraction["analysis_type"]
        has_companies = bool(company_name)
        
        # Persist extracted company name to session
        if has_companies:
            await db.update_session_metadata(
                session_id, user_id, company_name=company_name
            )
        
        # ── Query RAG for relevant document context ──
        doc_context = ""
        rag_service = getattr(request.app.state, "rag_service", None)
        if rag_service:
            try:
                rag_results = await rag_service.query(
                    query_text=body.message,
                    top_k=5,
                    namespace=f"user_{user_id}",
                )
                if rag_results:
                    chunks = [r["text"] for r in rag_results if r.get("text")]
                    if chunks:
                        doc_context = (
                            "\n\nRelevant context from uploaded documents:\n"
                            + "\n---\n".join(chunks[:5])
                            + "\n\nUse the above document context to inform your response when relevant."
                        )
            except Exception as rag_err:
                logger.warning("chat_rag_query_failed", error=str(rag_err))
        
        # Build chat history for LLM
        chat_history_text = "\n".join([
            f"{'User' if msg['role'] == 'user' else 'AI'}: {msg['content']}"
            for msg in messages
        ])
        
        # ── Build prompt based on conversation stage ──
        
        if user_messages_count == 1 and has_companies:
            # FIRST message with detected companies → confirm intent
            if analysis_type == "comparison" and len(companies) > 1:
                confirm_hint = (
                    f'The user seems to want to compare {" and ".join(companies)}. '
                    f'Ask a confirmation like: "Do you need me to compare {" and ".join(companies)}? '
                    f'I can look at their financials, market position, competitive strengths and more."'
                )
            elif analysis_type == "joint_venture" and len(companies) > 1:
                confirm_hint = (
                    f'The user is asking about a joint venture between {" and ".join(companies)}. '
                    f'Ask a confirmation like: "Would you like me to analyze the potential '
                    f'joint venture between {" and ".join(companies)}?"'
                )
            else:
                confirm_hint = (
                    f'The user is asking about {company_name}. '
                    f'Ask a specific confirmation like: "Do you need me to analyze {company_name}\'s '
                    f'financials, competitive landscape, and strategy?" '
                    f'Tailor the question to what the user seems interested in.'
                )
            
            prompt = f"""You are a helpful strategy analyst assistant for Origin Labs.

Current conversation:
{chat_history_text}
{doc_context}

{confirm_hint}

Rules:
- Be friendly and concise (1-3 sentences max)
- Confirm the company/companies detected and what kind of analysis the user wants
- Ask ONE follow-up question to clarify their specific goal (investment, competitive analysis, market entry, etc.)
- Do NOT directly start analyzing — just confirm and clarify

Respond naturally."""
        
        elif user_messages_count == 1 and not has_companies:
            # First message but no company detected — ask which company
            prompt = f"""You are a helpful strategy analyst assistant for Origin Labs.

Current conversation:
{chat_history_text}
{doc_context}

The user has not mentioned a specific company yet.
Ask them which company or companies they would like to analyze.
Be friendly and concise (1-2 sentences).

Respond naturally."""
        
        elif user_messages_count == 2:
            # Second exchange — one more clarifying question
            company_context = f"Companies detected: {', '.join(companies)}. " if has_companies else ""
            
            prompt = f"""You are a helpful strategy analyst assistant for Origin Labs.

Current conversation:
{chat_history_text}
{doc_context}

{company_context}Guidelines:
1. Acknowledge their response
2. Ask ONE final clarifying question about specifics (industry focus, time horizon, particular metrics, etc.)
3. Be friendly and concise (1-2 sentences)

Respond naturally with one follow-up question."""
        
        else:
            # 3+ exchanges — suggest starting analysis
            company_label = company_name if has_companies else "the company"
            
            prompt = f"""You are a helpful strategy analyst assistant for Origin Labs.

Current conversation:
{chat_history_text}
{doc_context}

You now have enough context. Suggest starting the comprehensive analysis for {company_label}.
Be enthusiastic and concise (1-2 sentences).
Example: "Great! I have everything I need. Shall I start the comprehensive analysis for {company_label}?"

Respond naturally."""
        
        try:
            ai_response = await llm.generate(
                prompt=prompt,
                task_type="extraction",
                temperature=0.7,
                max_tokens=200
            )
        except Exception as llm_error:
            logger.error("chat_llm_failed", error=str(llm_error), exc_info=True)
            ai_response = "I apologize, but I'm having trouble processing your message. Could you please try again?"
        
        # Add AI response to DB
        await db.add_message_to_session(session_id, user_id, "assistant", ai_response)
        
        total_messages = len(messages) + 1  # +1 for the AI response we just added
        ready_to_analyze = user_messages_count >= 2 and has_companies
        action = "ready_for_analysis" if ready_to_analyze else "continue_chat"
        
        return ChatResponse(
            session_id=session_id,
            message=ai_response,
            action=action,
            ready_to_analyze=ready_to_analyze,
            companies=companies,
            analysis_type=analysis_type,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("chat_message_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_from_chat(
    request: Request,
    body: StartAnalysisRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Trigger analysis from a chat session."""
    
    orchestrator = request.app.state.orchestrator
    pitch_deck_service = request.app.state.pitch_deck_service
    pdf_report_service = request.app.state.pdf_report_service
    db = request.app.state.db_service
    
    try:
        # Extract company names from chat history
        from app.routers._chat_utils import extract_company_names_from_chat
        
        if not body.company_name or body.company_name == "Company":
            extraction_result = await extract_company_names_from_chat(body.chat_history, request.app.state.llm_service)
            company_name = extraction_result["company_name"]
            companies = extraction_result["companies"]
            analysis_type = extraction_result["analysis_type"]
        else:
            company_name = body.company_name
            companies = [company_name]
            analysis_type = "single"
        
        # ── Query RAG for document context ──
        rag_chunks: list = []
        rag_service = getattr(request.app.state, "rag_service", None)
        if rag_service:
            try:
                rag_results = await rag_service.query(
                    query_text=f"{company_name} financial market strategy",
                    top_k=10,
                    namespace=f"user_{user_id}",
                )
                rag_chunks = [r["text"] for r in rag_results if r.get("text")]
            except Exception:
                pass
        
        else:
            company_name = body.company_name
            companies = [company_name]
            analysis_type = "single"
        
        logger.info(
            "chat_analysis_started",
            session_id=body.session_id,
            company=company_name,
            user_id=user_id
        )
        
        # Create initial state
        initial_state: AgentState = {
            "request": {
                "company_name": company_name,
                "companies": companies,
                "analysis_type": analysis_type,
                "industry": body.industry,
                "question": "Analysis based on chat conversation",
                "include_mna": False
            },
            "chat_history": [msg.dict() for msg in body.chat_history],
            "rag_context": rag_chunks,
            "errors": [],
            "metadata": {}
        }
        
        # Execute workflow
        final_state = await orchestrator.execute(initial_state)
        
        # Generate outputs
        output_urls = []
        
        if "pdf" in body.output_format or "json" in body.output_format:
            try:
                output_dir = "output/reports"
                os.makedirs(output_dir, exist_ok=True)
                pdf_filename = f"{company_name.replace(' ', '_')}_{int(time.time())}.pdf"
                pdf_path = os.path.join(output_dir, pdf_filename)
                await pdf_report_service.generate_report(
                    company_name=company_name,
                    analysis_data=final_state,
                    output_path=pdf_path
                )
                output_urls.append(pdf_path)
            except Exception as e:
                logger.error("pdf_generation_failed", error=str(e), exc_info=True)
        
        if "ppt" in body.output_format:
            try:
                output_dir = "output/decks"
                os.makedirs(output_dir, exist_ok=True)
                deck_filename = f"{company_name.replace(' ', '_')}_{int(time.time())}.pptx"
                deck_path = os.path.join(output_dir, deck_filename)
                await pitch_deck_service.generate_deck(
                    company_name=company_name,
                    analysis_data=final_state,
                    output_path=deck_path
                )
                output_urls.append(deck_path)
            except Exception as e:
                logger.error("deck_generation_failed", error=str(e), exc_info=True)
        
        # Build response
        analysis_id = f"analysis_{company_name}_{int(time.time())}"
        response = AnalysisResponse(
            analysis_id=analysis_id,
            company_name=company_name,
            status="completed" if not final_state.get("errors") else "completed_with_errors",
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            summary=final_state.get("strategy_synthesis", {}).get("executive_summary", ""),
            output_urls=output_urls,
            execution_time=final_state.get("metadata", {}).get("total_execution_time", 0),
            errors=final_state.get("errors", [])
        )
        
        # Save analysis to DB
        await db.save_analysis(user_id, {
            "_id": analysis_id,
            "company_name": company_name,
            "status": response.status,
            "summary": response.summary,
            "output_urls": output_urls,
            "execution_time": response.execution_time,
            "errors": response.errors,
            "session_id": body.session_id,
        })
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("chat_analysis_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Multi-Company Comparison ====================


class CompareRequest(BaseModel):
    session_id: str
    companies: List[str] = Field(..., min_length=2, max_length=3)
    industry: Optional[str] = None
    chat_history: List[ChatMessage] = []


class CompareDownloadRequest(BaseModel):
    comparison_id: str
    format: str = Field(..., description="'pdf' or 'ppt'")


@router.post("/compare")
async def compare_companies(
    request: Request,
    body: CompareRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    Run analysis for each company in parallel, then generate a side-by-side
    comparison table via the LLM.
    """
    orchestrator = request.app.state.orchestrator
    llm = request.app.state.llm_service
    db = request.app.state.db_service

    companies = [c.strip() for c in body.companies if c.strip()]
    if len(companies) < 2:
        raise HTTPException(status_code=400, detail="At least 2 companies required.")

    logger.info("comparison_started", companies=companies, user_id=user_id)

    # ── Query RAG for document context (shared across all companies) ──
    rag_chunks: list = []
    rag_service = getattr(request.app.state, "rag_service", None)
    if rag_service:
        try:
            rag_results = await rag_service.query(
                query_text=f"{' '.join(companies)} financial market strategy",
                top_k=10,
                namespace=f"user_{user_id}",
            )
            rag_chunks = [r["text"] for r in rag_results if r.get("text")]
        except Exception:
            pass

    # ── Run orchestrator for each company in parallel ──
    async def _run_single(company: str) -> Dict[str, Any]:
        state: AgentState = {
            "request": {
                "company_name": company,
                "companies": [company],
                "analysis_type": "single",
                "industry": body.industry,
                "question": "Full strategic analysis for comparison",
                "include_mna": False,
            },
            "chat_history": [msg.dict() for msg in body.chat_history],
            "rag_context": rag_chunks,
            "errors": [],
            "metadata": {},
        }
        return await orchestrator.execute(state)

    try:
        results = await asyncio.gather(
            *[_run_single(c) for c in companies],
            return_exceptions=True,
        )
    except Exception as e:
        logger.error("comparison_orchestrator_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Analysis failed.")

    # Collect per-company summaries for the LLM
    company_summaries: Dict[str, Dict[str, Any]] = {}
    errors: List[str] = []

    for idx, company in enumerate(companies):
        res = results[idx]
        if isinstance(res, Exception):
            errors.append(f"{company}: {str(res)}")
            company_summaries[company] = {"error": str(res)}
            continue

        company_summaries[company] = {
            "profile": res.get("company_profile", {}),
            "market": res.get("market_analysis", {}),
            "financial": res.get("financial_model", {}),
            "risk": res.get("risk_assessment", {}),
            "strategy": res.get("strategy_synthesis", {}),
        }

    # ── Build comparison table via LLM ──
    comparison_prompt = f"""You are a strategy analyst. Given the analysis data for {len(companies)} companies, create a structured comparison.

Companies analyzed: {', '.join(companies)}

Data per company:
{json.dumps(company_summaries, indent=2, default=str)[:12000]}

Generate a JSON object with this EXACT structure (no markdown, only raw JSON):
{{
  "title": "Comparison: {' vs '.join(companies)}",
  "categories": [
    {{
      "name": "Company Overview",
      "rows": [
        {{
          "metric": "<metric name>",
          {', '.join([f'"company_{i}": "<value for {c}>"' for i, c in enumerate(companies)])}
        }}
      ]
    }},
    {{
      "name": "Financial Highlights",
      "rows": [...]
    }},
    {{
      "name": "Market Position",
      "rows": [...]
    }},
    {{
      "name": "Strengths",
      "rows": [...]
    }},
    {{
      "name": "Weaknesses",
      "rows": [...]
    }},
    {{
      "name": "Key Risks",
      "rows": [...]
    }},
    {{
      "name": "Strategic Outlook",
      "rows": [...]
    }}
  ],
  "verdict": "<1-2 sentence overall verdict>"
}}

Rules:
1. Include 3-5 rows per category.
2. value format: Use concise strings (e.g. "$150B", "12%", "High").
3. CRITICAL: NEVER return "null", "zero", "0.00%", or "0" if data is missing.
   - If data is missing or zero, use "N/A" or estimate based on context.
   - For "Market Capitalization" or "Revenue", if specific numbers are missing, search the text for clues or use "N/A".
4. Return ONLY valid JSON.
"""

    try:
        comparison_raw = await llm.generate(
            prompt=comparison_prompt,
            task_type="extraction",
            temperature=0.3,
            max_tokens=3000,
        )

        # Parse JSON from response (strip markdown fences if present)
        clean = comparison_raw.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1]
            if clean.endswith("```"):
                clean = clean[:-3]
        comparison_data = json.loads(clean)

    except (json.JSONDecodeError, Exception) as e:
        logger.error("comparison_llm_parse_failed", error=str(e))
        # Fallback: build a minimal table from raw data
        comparison_data = {
            "title": f"Comparison: {' vs '.join(companies)}",
            "categories": [],
            "verdict": "Comparison data generated but formatting failed. See individual analyses.",
        }

    # ── Store in DB ──
    comparison_id = f"cmp_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    comparison_data["comparison_id"] = comparison_id
    comparison_data["companies"] = companies

    # Save to MongoDB
    await db.db.comparisons.insert_one({
        "_id": comparison_id,
        "user_id": user_id,
        "companies": companies,
        "comparison": comparison_data,
        "session_id": body.session_id,
        "created_at": datetime.utcnow().isoformat(),
    })

    logger.info("comparison_completed", comparison_id=comparison_id, companies=companies)

    return {
        "comparison_id": comparison_id,
        "comparison": comparison_data,
        "errors": errors,
    }


@router.post("/compare/download")
async def download_comparison(
    request: Request,
    body: CompareDownloadRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Generate or retrieve a persistent PDF/PPT report."""

    pdf_service = request.app.state.pdf_report_service
    deck_service = request.app.state.pitch_deck_service
    db = request.app.state.db_service

    # Fetch comparison from DB
    comparison = await db.get_comparison(body.comparison_id)
    if not comparison:
        # Fallback to cache if not in DB (legacy support)
        cached = _comparison_cache.get(body.comparison_id) # Using global cache if DB fails
        if not cached:
            raise HTTPException(status_code=404, detail="Comparison not found.")
        comparison = cached.get("comparison", cached)

    # Check if file already exists in GridFS
    file_key = f"{body.format}_file_id"
    existing_file_id = comparison.get(file_key)
    
    if existing_file_id:
        # Verify it actually exists
        if await db.get_file(existing_file_id):
            return {
                "download_url": f"/documents/download/{existing_file_id}",
                "filename": f"comparison.{body.format}" # Frontend might rename it
            }

    # Generate new file
    companies = comparison.get("companies", [])
    title = comparison.get("title", "Company Comparison")
    
    # Ensure output dir exists
    output_dir = f"output/{body.format}s"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = int(time.time())
    safe_names = "_vs_".join(c.replace(" ", "_") for c in companies)
    filename = f"comparison_{safe_names}_{timestamp}.{body.format}"
    output_path = os.path.join(output_dir, filename)
    
    try:
        if body.format == "pdf":
            await pdf_service.generate_comparison_report(
                title=title,
                companies=companies,
                comparison_data=comparison,
                output_path=output_path,
            )
            content_type = "application/pdf"
        elif body.format == "ppt":
            # Map ppt -> pptx
            if not filename.endswith(".pptx"):
                 filename += "x"
                 output_path += "x"
            
            await deck_service.generate_comparison_deck(
                title=title,
                companies=companies,
                comparison_data=comparison,
                output_path=output_path,
            )
            content_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        else:
            raise HTTPException(status_code=400, detail="Format must be 'pdf' or 'ppt'.")

        # Upload to GridFS
        with open(output_path, "rb") as f:
            file_data = f.read()
            
        file_id = await db.upload_file(
            filename=filename,
            data=file_data,
            content_type=content_type,
            metadata={"comparison_id": body.comparison_id, "user_id": user_id}
        )
        
        # Update comparison with file_id
        comparison[file_key] = file_id
        await db.save_comparison(comparison)
        
        logger.info("comparison_file_persisted", format=body.format, file_id=file_id)
        
        return {
            "download_url": f"/documents/download/{file_id}",
            "filename": filename
        }
        
    except Exception as e:
        logger.error("generation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


# ==================== Session Management Endpoints ====================


@router.get("/sessions", response_model=List[SessionListItem])
async def list_sessions(
    request: Request,
    user_id: str = Depends(get_current_user_id)
):
    """List all chat sessions for the current user (for sidebar)."""
    
    db = request.app.state.db_service
    sessions = await db.list_user_sessions(user_id)
    return sessions


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    request: Request,
    user_id: str = Depends(get_current_user_id)
):
    """Get a specific chat session with all messages."""
    
    db = request.app.state.db_service
    session = await db.get_chat_session(session_id, user_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "id": session["_id"],
        "title": session.get("title", "New Chat"),
        "company_name": session.get("company_name"),
        "industry": session.get("industry"),
        "messages": session.get("messages", []),
        "created_at": session.get("created_at", datetime.utcnow()).isoformat(),
        "updated_at": session.get("updated_at", datetime.utcnow()).isoformat(),
    }


@router.put("/sessions/{session_id}/title")
async def update_session_title(
    session_id: str,
    body: SessionTitleUpdate,
    request: Request,
    user_id: str = Depends(get_current_user_id)
):
    """Rename a chat session."""
    
    db = request.app.state.db_service
    success = await db.update_session_title(session_id, user_id, body.title)
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"status": "ok", "title": body.title}


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    request: Request,
    user_id: str = Depends(get_current_user_id)
):
    """Delete a chat session."""
    
    db = request.app.state.db_service
    success = await db.delete_chat_session(session_id, user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"status": "ok"}
