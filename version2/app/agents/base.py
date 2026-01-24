"""Base agent class for all agents."""

from abc import ABC, abstractmethod
from typing import Dict, Any
import time
from app.models.state import AgentState
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BaseAgent(ABC):
    """
    Base class for all agents in the system.
    
    Provides:
    - Standard execute interface
    - Error handling and logging
    - Execution time tracking
    - State validation
    """
    
    def __init__(self, name: str):
        """
        Initialize base agent.
        
        Args:
            name: Agent name (used for logging and tracking)
        """
        self.name = name
        logger.info(f"{name}_agent_initialized")
    
    @abstractmethod
    async def execute(self, state: AgentState) -> AgentState:
        """
        Execute agent logic and update state.
        
        This method must be implemented by all agents.
        
        Args:
            state: Current agent state
        
        Returns:
            Updated agent state
        """
        pass
    
    async def run(self, state: AgentState) -> AgentState:
        """
        Wrapper for execute with logging and error handling.
        
        Args:
            state: Current agent state
        
        Returns:
            Updated agent state
        """
        start_time = time.time()
        
        try:
            logger.info(f"{self.name}_started")
            
            # Execute agent logic
            result = await self.execute(state)
            
            # Track execution time
            execution_time = time.time() - start_time
            if "metadata" not in result:
                result["metadata"] = {}
            result["metadata"][f"{self.name}_time"] = execution_time
            
            logger.info(
                f"{self.name}_completed",
                execution_time=execution_time
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            logger.error(
                f"{self.name}_failed",
                error=str(e),
                execution_time=execution_time,
                exc_info=True
            )
            
            # Add error to state
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(f"{self.name}: {str(e)}")
            
            return state
    
    def _validate_state(self, state: AgentState, required_fields: list) -> bool:
        """
        Validate that required fields exist in state.
        
        Args:
            state: Agent state to validate
            required_fields: List of required field names
        
        Returns:
            True if all fields present, False otherwise
        """
        missing = [field for field in required_fields if field not in state]
        
        if missing:
            logger.warning(
                f"{self.name}_missing_required_fields",
                missing_fields=missing
            )
            return False
        
        return True
