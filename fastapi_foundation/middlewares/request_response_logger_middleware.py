import time
import json
import logging
from datetime import datetime
from fastapi import Request, BackgroundTasks
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger("request_response")

class RequestResponseLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(int(time.time() * 1000))
        
        # Log request details
        start_time = time.time()
        background_tasks = BackgroundTasks()
        request_body = await request.body()
        
        # Create structured log data
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "type": "request",
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_ip": request.client.host if request.client else None,
            "headers": self._sanitize_headers(dict(request.headers)),
            "body": request_body.decode("utf-8") if request_body else None,
        }
        
        # Log request as JSON
        background_tasks.add_task(self._log_data, log_data)
        
        user_agent_params = getattr(request.state, "user_agent_params", None)
            
        user_agent_params = json.dumps(user_agent_params.dict()) if user_agent_params else None

        try:
            # Call the next middleware/handler
            response = await call_next(request)
            
            # Capture response body
            response_body = [section async for section in response.body_iterator]
            response_body_content = b"".join(response_body).decode("utf-8")
            
            # Calculate processing time
            process_time = time.time() - start_time

            # Create structured response log
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "request_id": request_id,
                "type": "response",
                "status_code": response.status_code,
                "processing_time_ms": round(process_time * 1000),
                "headers": self._sanitize_headers(dict(response.headers)),
                "body": self._truncate_body(response_body_content),
                "user_agent_params": user_agent_params,
            }
            
            # Log response as JSON
            background_tasks.add_task(self._log_data, log_data)
            
            # Return the response
            return Response(
                content=response_body_content, 
                status_code=response.status_code, 
                headers=dict(response.headers),
                background=background_tasks
            )
            
        except Exception as e:
            # Log errors
            error_log = {
                "timestamp": datetime.now().isoformat(),
                "request_id": request_id,
                "type": "error",
                "error": str(e),
                "path": request.url.path,
                "method": request.method,
                "user_agent_params": user_agent_params
            }
            logger.error(json.dumps(error_log))
            raise

    def _log_data(self, data: dict):
        """Log the data as JSON for CloudWatch"""
        if data["type"] == "request":
            logger.info(json.dumps(data))
        else:
            logger.info(json.dumps(data))
            
    def _sanitize_headers(self, headers: dict) -> dict:
        """Remove sensitive information from headers"""
        sensitive_headers = ['authorization', 'cookie', 'x-api-key']
        sanitized = {}
        
        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
                
        return sanitized
        
    def _truncate_body(self, body: str, max_length: int = 1000) -> str:
        """Truncate body if it's too large"""
        if body and len(body) > max_length:
            return body[:max_length] + "... [truncated]"
        return body