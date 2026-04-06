"""
Error handling and retry utilities for PocketPro SBA.
"""
import logging
import time
import functools
from typing import Any, Callable, Dict, Optional, Type, Union
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    RetryError,
    before_log,
    after_log,
)

logger = logging.getLogger(__name__)

class RAGServiceError(Exception):
    """Base exception for RAG service errors."""
    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}

class ChromaDBError(RAGServiceError):
    """ChromaDB specific errors."""
    pass

class ValidationError(RAGServiceError):
    """Validation errors for input data."""
    pass

class RateLimitError(RAGServiceError):
    """Rate limit exceeded errors."""
    pass

def with_error_handling(
    error_map: Dict[Type[Exception], Type[RAGServiceError]] = None,
    max_retries: int = 3,
    retry_exceptions: tuple = (Exception,),
    log_errors: bool = True,
) -> Callable:
    """
    Decorator for handling errors and implementing retries.
    
    Args:
        error_map: Mapping of caught exceptions to custom exceptions
        max_retries: Maximum number of retry attempts
        retry_exceptions: Tuple of exceptions to retry on
        log_errors: Whether to log errors
    
    Returns:
        Decorated function with error handling and retries
    """
    error_map = error_map or {}

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        @retry(
            stop=stop_after_attempt(max_retries),
            wait=wait_exponential(multiplier=1, min=4, max=10),
            retry=retry_exceptions,
            before=before_log(logger, logging.DEBUG),
            after=after_log(logger, logging.DEBUG),
        )
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(
                        f"Error in {func.__name__}: {str(e)}",
                        exc_info=True,
                        extra={
                            "function": func.__name__,
                            "args": args,
                            "kwargs": kwargs,
                        }
                    )
                
                # Map exception to custom error if defined
                for caught_exc, custom_exc in error_map.items():
                    if isinstance(e, caught_exc):
                        raise custom_exc(str(e))
                
                # Re-raise the original exception if no mapping exists
                raise
        
        return wrapper
    
    return decorator

def rate_limit(
    max_calls: int,
    time_window: int,
    error_cls: Type[Exception] = RateLimitError
) -> Callable:
    """
    Rate limiting decorator.
    
    Args:
        max_calls: Maximum number of calls allowed in the time window
        time_window: Time window in seconds
        error_cls: Exception class to raise when rate limit is exceeded
    
    Returns:
        Decorated function with rate limiting
    """
    calls = []
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            now = time.time()
            
            # Remove old calls outside the time window
            while calls and calls[0] < now - time_window:
                calls.pop(0)
            
            if len(calls) >= max_calls:
                raise error_cls(
                    f"Rate limit exceeded. Maximum {max_calls} calls per {time_window} seconds."
                )
            
            calls.append(now)
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator

def validate_input(schema_cls: Any) -> Callable:
    """
    Input validation decorator using Pydantic schemas.
    
    Args:
        schema_cls: Pydantic model class for validation
    
    Returns:
        Decorated function with input validation
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                # Validate kwargs against schema
                validated_data = schema_cls(**kwargs)
                # Update kwargs with validated data
                kwargs.update(validated_data.dict())
                return func(*args, **kwargs)
            except Exception as e:
                raise ValidationError(f"Input validation failed: {str(e)}")
        
        return wrapper
    
    return decorator

# Error response formatter
def format_error_response(
    error: Exception,
    status_code: int = 500,
    include_details: bool = True
) -> Dict:
    """
    Format error responses consistently.
    
    Args:
        error: The exception to format
        status_code: HTTP status code
        include_details: Whether to include error details
    
    Returns:
        Formatted error response dictionary
    """
    response = {
        "error": True,
        "message": str(error),
        "status_code": status_code,
        "error_type": error.__class__.__name__,
        "timestamp": int(time.time())
    }
    
    if include_details and isinstance(error, RAGServiceError):
        if error.error_code:
            response["error_code"] = error.error_code
        if error.details:
            response["details"] = error.details
    
    return response