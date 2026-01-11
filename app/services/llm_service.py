"""LLM service for interacting with Groq API and OpenRouter fallback."""

from typing import Any, Dict, List, Optional
import json
import asyncio
from datetime import datetime

from groq import AsyncGroq, RateLimitError, APIError
from openai import AsyncOpenAI

from app.services.rate_limiter import RateLimiter
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LLMService:
    """
    LLM service with multi-provider support (Groq primary, OpenRouter fallback).
    Includes rate limiting, retry logic, and automatic fallback on errors.
    """
    
    def __init__(
        self,
        groq_api_key: str,
        openrouter_api_key: Optional[str] = None,
        groq_model: str = "llama-3.3-70b-versatile",
        openrouter_model: str = "google/gemini-2.0-flash-exp:free",
        openrouter_site_url: str = "",
        openrouter_site_name: str = "Enterprise Strategy Platform",
        max_retries: int = 3,
        retry_delay: float = 2.0,
        rate_limit_delay: float = 1.0
    ) -> None:
        """
        Initialize LLM service with multi-provider support.
        
        Args:
            groq_api_key: Groq API key (primary provider)
            openrouter_api_key: OpenRouter API key (fallback provider)
            groq_model: Groq model name
            openrouter_model: OpenRouter model name
            openrouter_site_url: Site URL for OpenRouter rankings
            openrouter_site_name: Site name for OpenRouter rankings
            max_retries: Maximum retry attempts
            retry_delay: Initial retry delay (exponential backoff)
            rate_limit_delay: Delay between requests to prevent rate limiting
        """
        self.groq_api_key = groq_api_key
        self.openrouter_api_key = openrouter_api_key
        self.groq_model = groq_model
        self.openrouter_model = openrouter_model
        self.openrouter_site_url = openrouter_site_url
        self.openrouter_site_name = openrouter_site_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.rate_limit_delay = rate_limit_delay
        
        # Initialize Groq client with retries disabled (we handle retries ourselves)
        self.groq_client = AsyncGroq(
            api_key=groq_api_key,
            max_retries=0  # Disable Groq's built-in retry to allow our fallback logic
        )
        
        # Initialize OpenRouter client if API key provided
        self.openrouter_client = None
        if openrouter_api_key:
            self.openrouter_client = AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=openrouter_api_key
            )
        
        # Track last request time for rate limiting
        self.last_request_time = None
        
        # Track provider health
        self.groq_available = True
        self.openrouter_available = bool(openrouter_api_key)
        
        # Initialize rate limiter for free tier
        # Groq free tier: 14,400 TPM, ~30 RPM (but we use 10 to be safe)
        self.rate_limiter = RateLimiter(
            calls_per_minute=10,
            tokens_per_minute=14400,  # Groq free tier TPM limit
            min_delay_seconds=5.0     # Conservative delay
        )
        
        logger.info(
            "llm_service_initialized",
            groq_model=groq_model,
            openrouter_model=openrouter_model,
            has_fallback=self.openrouter_available,
            rate_limit="10 RPM, 14400 TPM, 5s min delay"
        )
    
    def _extract_wait_time(self, error_message: str) -> float:
        """
        Extract wait time from rate limit error message.
        
        Parses messages like:
        - "Please try again in 779.999999ms"
        - "Please try again in 7.28s"
        
        Args:
            error_message: The error message from the API
            
        Returns:
            Wait time in seconds, or 0 if not found
        """
        import re
        
        # Look for "try again in X.XXms" or "try again in X.XXs"
        patterns = [
            r'try again in (\d+\.?\d*)ms',   # milliseconds
            r'try again in (\d+\.?\d*)s',    # seconds
            r'Please retry in (\d+\.?\d*)s', # alternative format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_message, re.IGNORECASE)
            if match:
                value = float(match.group(1))
                # Convert ms to seconds if needed
                if 'ms' in pattern:
                    value = value / 1000
                # Add small buffer
                return value + 0.5
        
        return 0.0
    
    async def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        if self.last_request_time and self.rate_limit_delay > 0:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            if elapsed < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = datetime.now()
    
    async def _call_groq(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Call Groq API."""
        response = await self.groq_client.chat.completions.create(
            model=self.groq_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    
    async def _call_openrouter(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Call OpenRouter API."""
        if not self.openrouter_client:
            raise ValueError("OpenRouter client not initialized")
        
        extra_headers = {}
        if self.openrouter_site_url:
            extra_headers["HTTP-Referer"] = self.openrouter_site_url
        if self.openrouter_site_name:
            extra_headers["X-Title"] = self.openrouter_site_name
        
        response = await self.openrouter_client.chat.completions.create(
            model=self.openrouter_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            extra_headers=extra_headers if extra_headers else None
        )
        return response.choices[0].message.content
    
    async def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """
        Generate text using LLM with automatic fallback and retry logic.
        
        Args:
            prompt: User prompt
            system_message: Optional system message
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        # Apply rate limiting (enforces minimum delay and calls/minute limit)
        # Pass prompt length for token estimation
        await self.rate_limiter.acquire(estimated_prompt_length=len(prompt))
        
        # Build messages
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
        
        # Retry loop with proper rate limit handling
        attempts = 0
        last_error = None
        
        while attempts < self.max_retries:
            attempts += 1
            
            # Always reset groq_available at start of each attempt
            # (it may have been marked unavailable in previous attempt)
            if attempts > 1:
                self.groq_available = True
            
            # Try Groq first
            try:
                result = await self._call_groq(messages, temperature, max_tokens)
                logger.debug(
                    "llm_generation_complete",
                    provider="groq",
                    prompt_length=len(prompt),
                    response_length=len(result)
                )
                return result
                
            except (RateLimitError, Exception) as e:
                error_str = str(e).lower()
                is_rate_limit = (
                    isinstance(e, RateLimitError) or
                    "429" in error_str or 
                    "rate limit" in error_str or 
                    "too many requests" in error_str
                )
                
                if is_rate_limit:
                    # Extract wait time from error message
                    wait_time = self._extract_wait_time(str(e))
                    
                    logger.warning(
                        "groq_rate_limit_hit",
                        attempt=attempts,
                        max_attempts=self.max_retries,
                        wait_time=wait_time,
                        error=str(e)[:200]
                    )
                    
                    # Try OpenRouter if available
                    if self.openrouter_available:
                        try:
                            result = await self._call_openrouter(messages, temperature, max_tokens)
                            logger.info(
                                "llm_generation_complete_fallback",
                                provider="openrouter"
                            )
                            return result
                        except Exception as or_error:
                            logger.warning(
                                "openrouter_also_failed",
                                error=str(or_error)[:200]
                            )
                            # Fall through to wait and retry Groq
                    
                    # Wait before retrying Groq
                    if attempts < self.max_retries:
                        if wait_time > 0:
                            # Use the wait time from error message
                            logger.info("waiting_for_rate_limit_reset", wait_seconds=wait_time)
                            await asyncio.sleep(wait_time)
                        else:
                            # Use exponential backoff
                            delay = self.retry_delay * (2 ** (attempts - 1))
                            delay = min(delay, 30)  # Cap at 30 seconds
                            logger.info("waiting_with_backoff", delay=delay)
                            await asyncio.sleep(delay)
                        continue
                    else:
                        last_error = e
                else:
                    # Non-rate-limit error
                    last_error = e
                    logger.error("llm_non_rate_limit_error", error=str(e))
                    
                    # For non-rate-limit errors, wait and retry
                    if attempts < self.max_retries:
                        delay = self.retry_delay * attempts
                        await asyncio.sleep(delay)
                        continue
        
        # All retries exhausted
        logger.error(
            "llm_generation_failed_all_retries",
            attempts=attempts,
            error=str(last_error) if last_error else "Unknown error"
        )
        raise last_error or ValueError("LLM generation failed after all retries")
    
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

