# frontend/logger.py
import asyncio
import logging
import sys
import functools
from typing import Callable, Any



def setup_logging() -> logging.Logger:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - frontend - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger("frontend")


def log_call(logger: logging.Logger) -> Callable[..., Callable[..., Any]]:
    """Decorator to log function entry/exit with module and function name."""
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

# Create default logger
logger = setup_logging()

