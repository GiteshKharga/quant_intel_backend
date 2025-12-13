
import functools
import logging
import time
from typing import Callable, Any
from app.core.result import Result

logger = logging.getLogger("quant_intel_core")

def robust_service(name: str = None):
    """
    Decorator to convert a function into a Robust Service.
    - Catches ALL exceptions
    - Logs execution time and errors
    - Returns a Result object (Success/Failure)
    - Eliminates the need for try/except blocks in business logic
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Result:
            service_name = name or func.__name__
            start_time = time.time()
            
            try:
                # Execute Business Logic
                val = func(*args, **kwargs)
                
                # Performance Logging
                duration = (time.time() - start_time) * 1000
                if duration > 500: # Log slow queries
                    logger.warning(f"🐢 Slow Service: {service_name} took {duration:.2f}ms")
                
                # If function already returned a Result, pass it through
                if isinstance(val, Result):
                    return val
                    
                # Otherwise wrap in Success
                return Result.Ok(val)

            except Exception as e:
                # Centralized Error Handling
                duration = (time.time() - start_time) * 1000
                logger.error(f"❌ Service Failure: {service_name} failed in {duration:.2f}ms | Error: {str(e)}", exc_info=True)
                return Result.Fail(str(e))
                
        return wrapper
    return decorator
