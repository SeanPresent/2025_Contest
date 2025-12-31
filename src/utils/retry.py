"""Retry utilities with exponential backoff"""

import time
import random
from functools import wraps
from typing import Callable, TypeVar, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError
)

T = TypeVar('T')

# Common exceptions to retry
RETRYABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    Exception  # Generic fallback
)


def retry_with_backoff(
    max_attempts: int = 3,
    initial_wait: float = 1.0,
    max_wait: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True
):
    """
    Decorator for retrying functions with exponential backoff
    
    Args:
        max_attempts: Maximum number of retry attempts
        initial_wait: Initial wait time in seconds
        max_wait: Maximum wait time in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter to wait time
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(
                multiplier=initial_wait,
                max=max_wait,
                exp_base=exponential_base
            ),
            retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
            reraise=True
        )
        def wrapper(*args: Any, **kwargs: Any) -> T:
            if jitter:
                # Add small random jitter to avoid thundering herd
                time.sleep(random.uniform(0, 0.5))
            return func(*args, **kwargs)
        return wrapper
    return decorator


def simple_retry(max_attempts: int = 3, delay: float = 1.0):
    """Simple retry decorator with fixed delay"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay * (attempt + 1))
                    else:
                        raise
            if last_exception:
                raise last_exception
        return wrapper
    return decorator

