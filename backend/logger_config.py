# backend\logger_config.py

# Standard library imports
import sys
import functools
import asyncio

# Third-party imports
import logging

# Typing imports
from typing import Optional, Callable, Any

def setup_logging(level: str = "INFO", log_format: Optional[str] = None) -> logging.Logger:
    """Setup logging configuration for the application and return the app logger."""
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Configure root logger handlers (only once)
    root = logging.getLogger()
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(log_format)
        handler.setFormatter(formatter)
        root.setLevel(getattr(logging, level.upper(), logging.INFO))
        root.addHandler(handler)

    # Create/get application logger
    logger = logging.getLogger("ai_social_post")
    # Keep application-level logs at INFO by default to avoid very noisy ENTER/EXIT debug spam
    logger.setLevel(logging.INFO)

    # Reduce verbosity for noisy third-party libraries
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    logging.getLogger('langchain').setLevel(logging.WARNING)
    logging.getLogger('google').setLevel(logging.WARNING)
    return logger

def log_call(logger: logging.Logger) -> Callable[..., Callable[..., Any]]:
    """Decorator factory that logs entry/exit and exceptions for sync and async functions.

    Usage: 
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                logger.debug(f"ENTER {func.__module__}.{func.__name__}() args={len(args)} kwargs={list(kwargs.keys())}")
                try:
                    result = await func(*args, **kwargs)
                    logger.debug(f"EXIT  {func.__module__}.{func.__name__}() ok")
                    return result
                except Exception as exc:
                    logger.exception(f"ERROR {func.__module__}.{func.__name__}() -> {exc}")
                    raise
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                logger.debug(f"ENTER {func.__module__}.{func.__name__}() args={len(args)} kwargs={list(kwargs.keys())}")
                try:
                    result = func(*args, **kwargs)
                    logger.debug(f"EXIT  {func.__module__}.{func.__name__}() ok")
                    return result
                except Exception as exc:
                    logger.exception(f"ERROR {func.__module__}.{func.__name__}() -> {exc}")
                    raise
            return sync_wrapper
    return decorator

# Module-level logger instance
logger = setup_logging()