"""
Timeout utilities for preventing timeout errors
"""
import asyncio
import functools
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)


def with_timeout(timeout_seconds: float, default_return: Any = None, error_message: str = "Operation timed out"):
    """
    Decorator to add timeout to async functions
    
    Args:
        timeout_seconds: Maximum time to wait
        default_return: Value to return on timeout
        error_message: Error message to log
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                logger.error(f"{error_message} (function: {func.__name__}, timeout: {timeout_seconds}s)")
                return default_return
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                raise
        return wrapper
    return decorator


async def run_with_timeout(
    coro,
    timeout: float,
    default_return: Any = None,
    error_message: str = "Operation timed out"
) -> Any:
    """
    Run a coroutine with timeout
    
    Args:
        coro: Coroutine to run
        timeout: Maximum time to wait
        default_return: Value to return on timeout
        error_message: Error message to log
        
    Returns:
        Result of coroutine or default_return on timeout
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.error(f"{error_message} (timeout: {timeout}s)")
        return default_return
    except Exception as e:
        logger.error(f"Error in coroutine: {e}")
        raise


async def retry_with_timeout(
    coro_factory: Callable,
    max_retries: int = 3,
    timeout_per_attempt: float = 30.0,
    default_return: Any = None
) -> Any:
    """
    Retry a coroutine with timeout on each attempt
    
    Args:
        coro_factory: Function that returns a coroutine (for retries)
        max_retries: Maximum number of retry attempts
        timeout_per_attempt: Timeout for each attempt
        default_return: Value to return if all retries fail
        
    Returns:
        Result of successful coroutine or default_return
    """
    last_error = None
    
    for attempt in range(max_retries):
        try:
            coro = coro_factory()
            result = await asyncio.wait_for(coro, timeout=timeout_per_attempt)
            if attempt > 0:
                logger.info(f"Retry succeeded on attempt {attempt + 1}")
            return result
        except asyncio.TimeoutError:
            last_error = f"Timeout on attempt {attempt + 1}/{max_retries}"
            logger.warning(last_error)
            if attempt < max_retries - 1:
                await asyncio.sleep(1)  # Brief delay before retry
        except Exception as e:
            last_error = f"Error on attempt {attempt + 1}: {str(e)}"
            logger.warning(last_error)
            if attempt < max_retries - 1:
                await asyncio.sleep(1)
    
    logger.error(f"All retries failed. Last error: {last_error}")
    return default_return
