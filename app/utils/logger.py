"""Structured logging configuration using structlog."""

import logging
import sys
from typing import Any, Dict, Optional

import structlog
from structlog.types import EventDict, Processor

from app.config import get_settings


def add_app_context(
    logger: logging.Logger, method_name: str, event_dict: EventDict
) -> EventDict:
    """
    Add application context to log events.
    
    Args:
        logger: Logger instance
        method_name: Method name
        event_dict: Event dictionary
        
    Returns:
        Updated event dictionary
    """
    event_dict["app"] = "stratagem_ai"
    event_dict["version"] = "1.0.0"
    return event_dict


def configure_logging(log_level: str = "INFO") -> None:
    """
    Configure structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            add_app_context,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(
    name: str,
    request_id: Optional[str] = None,
    agent_name: Optional[str] = None,
    **kwargs: Any
) -> structlog.stdlib.BoundLogger:
    """
    Get a configured logger instance with context.
    
    Args:
        name: Logger name (typically __name__)
        request_id: Optional request ID for tracing
        agent_name: Optional agent name for agent-specific logs
        **kwargs: Additional context fields
        
    Returns:
        Configured structlog logger
    """
    logger = structlog.get_logger(name)
    
    # Bind context
    context: Dict[str, Any] = {}
    if request_id:
        context["request_id"] = request_id
    if agent_name:
        context["agent_name"] = agent_name
    if kwargs:
        context.update(kwargs)
    
    if context:
        logger = logger.bind(**context)
    
    return logger


# Initialize logging on module import
try:
    settings = get_settings()
    configure_logging(settings.log_level)
except Exception:
    # Fallback to INFO if settings can't be loaded
    configure_logging("INFO")
