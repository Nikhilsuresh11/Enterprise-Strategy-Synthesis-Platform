"""Utility functions for chat — LLM-based company extraction."""

import json
from typing import Dict, List, Any
from app.models.chat_schemas import ChatMessage


async def extract_company_names_from_chat(
    messages: List[ChatMessage],
    llm_service,
) -> Dict[str, Any]:
    """
    Use the LLM to extract company names and determine analysis type
    from the conversation so far.

    Returns:
        {
          "companies": ["Company A", "Company B"],
          "analysis_type": "single" | "comparison" | "joint_venture",
          "company_name": "Company A" or "Company A vs Company B"
        }
    """

    # Concatenate all user messages
    user_text = "\n".join(
        msg.content for msg in messages if msg.role == "user"
    )

    if not user_text.strip():
        return _empty()

    prompt = f"""Extract company names from the following user messages.

User messages:
\"\"\"
{user_text}
\"\"\"

Return ONLY a JSON object with these fields (no markdown, no explanation):
{{
  "companies": ["<company name 1>", "<company name 2 if any>"],
  "analysis_type": "<one of: single, comparison, joint_venture>"
}}

Rules:
- Include only real company/brand names (e.g. "Tata Motors", "Hyundai", "Apple").
- Do NOT include generic words like "Market", "Industry", "Company", or action words.
- If the user wants to compare two companies, set analysis_type to "comparison".
- If the user mentions a joint venture or partnership, set analysis_type to "joint_venture".
- If only one company, set analysis_type to "single".
- Return at most 3 companies.
- Return ONLY valid JSON."""

    try:
        raw = await llm_service.generate(
            prompt=prompt,
            task_type="extraction",
            temperature=0.0,
            max_tokens=200,
        )

        # Parse — strip markdown fences if present
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1]
            if clean.endswith("```"):
                clean = clean[:-3]
        clean = clean.strip()

        data = json.loads(clean)
        companies = [c.strip() for c in data.get("companies", []) if c.strip()][:3]
        analysis_type = data.get("analysis_type", "single")

        if not companies:
            return _empty()

        if len(companies) == 1:
            company_name = companies[0]
            analysis_type = "single"
        elif analysis_type == "joint_venture":
            company_name = " + ".join(companies)
        else:
            company_name = " vs ".join(companies)

        return {
            "companies": companies,
            "analysis_type": analysis_type,
            "company_name": company_name,
        }

    except Exception:
        # If LLM fails, return empty rather than crash
        return _empty()


def _empty() -> Dict[str, Any]:
    return {
        "companies": [],
        "analysis_type": "single",
        "company_name": "",
    }
