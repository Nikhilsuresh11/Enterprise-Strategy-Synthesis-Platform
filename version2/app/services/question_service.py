"""Question Generation Service - Generates clarifying questions for better analysis."""

from typing import List, Dict, Any
from app.services.llm_service import LLMService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class QuestionService:
    """
    Service for generating clarifying questions to improve analysis quality.
    
    Features:
    - Generates 2-3 targeted questions based on user query
    - Focuses on: analysis goal, time horizon, specific concerns
    - Helps gather context for more relevant insights
    """
    
    def __init__(self, llm: LLMService):
        self.llm = llm
        logger.info("question_service_initialized")
    
    async def generate_questions(
        self,
        company_name: str,
        industry: str,
        question: str
    ) -> List[Dict[str, Any]]:
        """
        Generate 2-3 clarifying questions based on user's query.
        
        Args:
            company_name: Name of the company
            industry: Industry sector
            question: User's strategic question
        
        Returns:
            List of questions with options
        """
        logger.info("generating_clarifying_questions", company=company_name)
        
        prompt = f"""Generate 2-3 CLARIFYING QUESTIONS to improve the strategic analysis for {company_name}.

User's Question: "{question}"
Industry: {industry or "Unknown"}

Generate questions that will help provide more relevant, targeted insights. Focus on:
1. Analysis goal (investment, partnership, competitive analysis, etc.)
2. Time horizon (short-term vs long-term)
3. Specific areas of concern or interest

Return ONLY a JSON object:
{{
    "questions": [
        {{
            "question": "What is your primary goal for this analysis?",
            "options": [
                "Investment decision",
                "Partnership evaluation",
                "Competitive intelligence",
                "Market entry strategy",
                "Other"
            ]
        }},
        {{
            "question": "What time horizon are you most interested in?",
            "options": [
                "Immediate (0-6 months)",
                "Short-term (6-18 months)",
                "Medium-term (1-3 years)",
                "Long-term (3+ years)"
            ]
        }},
        {{
            "question": "Which aspect is most critical for your decision?",
            "options": [
                "Financial performance",
                "Market position",
                "Growth potential",
                "Risk factors",
                "Innovation capability"
            ]
        }}
    ]
}}

Keep questions concise and options clear. Generate exactly 2-3 questions.
"""
        
        response = await self.llm.generate(
            prompt=prompt,
            task_type="extraction",  # Use fast model
            temperature=0.3,
            max_tokens=500
        )
        
        # Parse JSON
        try:
            import json
            import re
            
            try:
                data = json.loads(response)
            except json.JSONDecodeError:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(0))
                else:
                    raise
            
            questions = data.get("questions", [])
            
            # Ensure we have 2-3 questions
            if len(questions) < 2:
                questions = self._get_default_questions()
            elif len(questions) > 3:
                questions = questions[:3]
            
            logger.info("questions_generated", count=len(questions))
            return questions
            
        except (json.JSONDecodeError, Exception) as e:
            logger.warning("question_generation_failed", error=str(e))
            return self._get_default_questions()
    
    def _get_default_questions(self) -> List[Dict[str, Any]]:
        """Return default clarifying questions."""
        return [
            {
                "question": "What is your primary goal for this analysis?",
                "options": [
                    "Investment decision",
                    "Partnership evaluation",
                    "Competitive intelligence",
                    "Market entry strategy",
                    "General research"
                ]
            },
            {
                "question": "What time horizon are you most interested in?",
                "options": [
                    "Immediate (0-6 months)",
                    "Short-term (6-18 months)",
                    "Medium-term (1-3 years)",
                    "Long-term (3+ years)"
                ]
            },
            {
                "question": "Which aspect is most critical?",
                "options": [
                    "Financial performance",
                    "Market position & growth",
                    "Risk factors",
                    "Innovation & technology"
                ]
            }
        ]
