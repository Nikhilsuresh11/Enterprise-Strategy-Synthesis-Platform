"""LLM service for interacting with Groq API."""

from typing import Any, Dict, List, Optional
import json

from groq import AsyncGroq

from app.utils.logger import get_logger

logger = get_logger(__name__)


class LLMService:
    """
    LLM service for generating content using Groq API (Mixtral model).
    """
    
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile") -> None:
        """
        Initialize LLM service.
        
        Args:
            api_key: Groq API key
            model: Model name to use (default: llama-3.3-70b-versatile)
        """
        self.api_key = api_key
        self.model = model
        self.client = AsyncGroq(api_key=api_key)
        
        logger.info("llm_service_initialized", model=model)
    
    async def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """
        Generate text using LLM.
        
        Args:
            prompt: User prompt
            system_message: Optional system message
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        try:
            messages = []
            
            if system_message:
                messages.append({
                    "role": "system",
                    "content": system_message
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            result = response.choices[0].message.content
            
            logger.debug(
                "llm_generation_complete",
                prompt_length=len(prompt),
                response_length=len(result)
            )
            
            return result
            
        except Exception as e:
            logger.error("llm_generation_failed", error=str(e))
            raise
    
    async def generate_structured_output(
        self,
        prompt: str,
        system_prompt: str,
        response_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate structured JSON output from LLM.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt describing the task
            response_schema: Expected JSON schema
            
        Returns:
            Structured output matching schema
        """
        try:
            # Add JSON formatting instruction
            enhanced_system = (
                f"{system_prompt}\n\n"
                f"You must respond with valid JSON matching this schema:\n"
                f"{json.dumps(response_schema, indent=2)}\n\n"
                f"Respond ONLY with the JSON object, no additional text."
            )
            
            response_text = await self.generate(
                prompt=prompt,
                system_message=enhanced_system,
                temperature=0.3  # Lower temperature for structured output
            )
            
            # Parse JSON
            try:
                result = json.loads(response_text)
                return result
            except json.JSONDecodeError:
                # Try to extract JSON from response
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                if start != -1 and end > start:
                    json_str = response_text[start:end]
                    result = json.loads(json_str)
                    return result
                raise
            
        except Exception as e:
            logger.error("structured_generation_failed", error=str(e))
            raise
    
    async def analyze_with_context(
        self,
        query: str,
        context: str,
        agent_role: str
    ) -> str:
        """
        Main analysis method with RAG context.
        
        Args:
            query: Analysis query
            context: Retrieved RAG context
            agent_role: Role of the agent (researcher, analyst, etc.)
            
        Returns:
            Analysis result
        """
        system_prompts = {
            "researcher": (
                "You are a senior research analyst at McKinsey & Company. "
                "Analyze the provided context and query to deliver insights "
                "backed by data and credible sources."
            ),
            "analyst": (
                "You are a financial analyst at McKinsey & Company. "
                "Provide detailed financial analysis with quantitative insights, "
                "market sizing, and strategic recommendations."
            ),
            "regulatory": (
                "You are a regulatory compliance expert at McKinsey & Company. "
                "Analyze regulatory requirements, compliance risks, and "
                "provide actionable recommendations."
            ),
            "synthesizer": (
                "You are a senior partner at McKinsey & Company. "
                "Synthesize all analysis into clear, actionable strategic "
                "recommendations for C-level executives."
            )
        }
        
        system_prompt = system_prompts.get(
            agent_role,
            "You are a management consultant at McKinsey & Company."
        )
        
        enhanced_prompt = (
            f"Context from knowledge base:\n\n{context}\n\n"
            f"Query: {query}\n\n"
            f"Provide a comprehensive analysis based on the context above."
        )
        
        return await self.generate(
            prompt=enhanced_prompt,
            system_message=system_prompt,
            temperature=0.7,
            max_tokens=2048
        )
    
    async def extract_entities(
        self,
        text: str
    ) -> Dict[str, List[str]]:
        """
        Extract entities from text.
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with entity types and values
        """
        schema = {
            "companies": ["list", "of", "company", "names"],
            "people": ["list", "of", "person", "names"],
            "locations": ["list", "of", "locations"],
            "dates": ["list", "of", "dates"],
            "numbers": ["list", "of", "important", "numbers"]
        }
        
        system_prompt = (
            "You are an expert at extracting structured information from text. "
            "Extract all relevant entities and return them in the specified JSON format."
        )
        
        prompt = f"Extract entities from this text:\n\n{text}"
        
        try:
            result = await self.generate_structured_output(
                prompt=prompt,
                system_prompt=system_prompt,
                response_schema=schema
            )
            return result
        except Exception as e:
            logger.error("entity_extraction_failed", error=str(e))
            # Return empty structure on failure
            return {
                "companies": [],
                "people": [],
                "locations": [],
                "dates": [],
                "numbers": []
            }
