import traceback
from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

from fastapi_foundation.utils.error_handler_utils import get_error_title

class GlobalExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        error_status_code = None
        error_response = None
        
        try:
            return await call_next(request)
        except HTTPException as e:
            traceback.print_exc()
            error_status_code = e.status_code
            error_response = {
                "status": "error",
                "code": error_status_code,
                "error": {
                    "message": "Bad Request",
                    "title": get_error_title(e.status_code),
                    "description": {
                        "errors": [{"message": e.detail or str(e)}]
                    }
                },
                "data": None
            }
        except Exception as e:
            traceback.print_exc()
            error_status_code = 500
            error_response = {
                "status": "error",
                "code": error_status_code,
                "error": {
                    "message": "Internal Server Error",
                    "title": get_error_title(error_status_code),
                    "description": {
                        "errors": [{"message": str(e)}]
                    }
                },
                "data": None
            }
        
        # Only execute if an exception was caught
        if error_response is not None:
            return JSONResponse(
                status_code=error_status_code,
                content=error_response
            )