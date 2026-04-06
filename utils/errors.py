import logging
from functools import wraps

logger = logging.getLogger(__name__)

class AppError(Exception):
    """Base exception for application errors."""
    pass

class DatabaseError(AppError):
    """Exception for database-related errors."""
    pass

class CacheError(AppError):
    """Exception for caching errors."""
    pass

def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            raise AppError(f"An error occurred: {str(e)}") from e
    return wrapper
