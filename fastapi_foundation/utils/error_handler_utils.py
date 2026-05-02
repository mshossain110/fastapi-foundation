import inspect
import traceback
from fastapi import HTTPException
from functools import wraps
from typing import Callable, Type, TypeVar, Any
from fastapi_foundation.models.api_response import ApiResponse
import asyncio
import random


async def execute_with_error_handling(callable_func, *args, **kwargs):
    try:
        if inspect.iscoroutinefunction(callable_func):
            result = await callable_func(*args, **kwargs)
        else:
            result = callable_func(*args, **kwargs)
        return result
    except HTTPException as e:
        traceback.print_exc()
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code= 400, detail=str(e))



T = TypeVar('T')
        

def api_response_wrapper(response_model: Type[T], success_code=200):
    """
    Decorator to wrap endpoint responses in ApiResponse format with error handling.
    
    Args:
        response_model: The expected response model type
        success_code: The HTTP status code to return on success (default is 200)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                
                # Execute the original function
                result = await func(*args, **kwargs)
                
                # If result is already an ApiResponse, return it
                if isinstance(result, ApiResponse):
                    return result
                
                # Wrap the result in ApiResponse
                return ApiResponse[response_model](
                    status="success",
                    code=success_code,
                    data=result
                )
            except Exception as e:
                traceback.print_exc()
                raise e
        return async_wrapper
    
    return decorator


def retry_async(attempts: int = 3, delay: float = 1.0, jitter: float = 1.0):
    """
    Retry async function on any exception.

    :param attempts: Number of attempts (total = initial + retries).
    :param delay: Base delay between retries in seconds.
    :param jitter: Max jitter to add to delay (uniformly random from 0 to jitter).
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < attempts:
                        sleep_time = delay + random.uniform(0, jitter)
                        await asyncio.sleep(sleep_time)
                    else:
                        raise last_exception
        return wrapper
    return decorator


def get_error_title(status_code: int) -> str:
    """Get appropriate error title based on status code."""
    titles = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        422: "Unprocessable Entity",
        429: "Too Many Requests",
        500: "Internal Server Error",
        502: "Bad Gateway",
        503: "Service Unavailable",
        504: "Gateway Timeout"
    }
    return titles.get(status_code, "Error")