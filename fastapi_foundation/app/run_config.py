import traceback
from fastapi_foundation.middlewares.request_response_logger_middleware import RequestResponseLoggerMiddleware
from fastapi_foundation.middlewares.user_agent_middleware import UserAgentMiddleware
from fastapi_foundation.routers import info_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException, Request, status
from scalar_fastapi import get_scalar_api_reference

import multiprocessing
import uvicorn
from uvicorn.config import LOGGING_CONFIG
from typing import Dict, Any
import logging
from fastapi_foundation.middlewares.global_exception_handler import GlobalExceptionMiddleware
from fastapi.responses import JSONResponse

from fastapi_foundation.app import FastAPIFoundation

import os
import logging

from fastapi_foundation.utils.error_handler_utils import get_error_title
logger = logging.getLogger(__name__)


# Print all configuration values
def print_all_config():
    logging.info("Configuration values:")

    # Get all environment variables that were loaded
    for key, value in os.environ.items():
        logging.info(f"{key}: {value}")


def create_scalar_doc(app: FastAPIFoundation):
    @app.get('/scalar', include_in_schema=False)
    async def scaler_html():
        return get_scalar_api_reference(
            openapi_url=app.openapi_url,
            title=app.title + "- Scalar"
        )


def add_common_wrappers(
    app: FastAPIFoundation,
    disable_ua_enforse: bool = False,
    disable_logger: bool = False,
) -> FastAPIFoundation:
    # print_all_config()
    app.add_middleware(GlobalExceptionMiddleware)

    @app.exception_handler(HTTPException)
    async def handel_http_exceptions(request: Request, e: HTTPException):
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

        return JSONResponse(
            status_code=error_status_code,
            content=error_response
        )

    # Define a function to handle validation errors
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # Transform the validation errors into your ErrorDescription format
        error_items = []
        for error in exc.errors():
            location = " -> ".join(str(loc) for loc in error.get("loc", []))
            message = f"{location}: {error.get('msg', 'Unknown error')}"
            error_items.append({"message": message})

        # Create the ApiResponse structure
        error_response = {
            "status": "error",
            "code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "error": {
                "message": "Validation Error",
                "title": "Invalid Input",
                "description": {
                    "errors": error_items
                }
            },
            "data": None
        }

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response,
        )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    if not disable_ua_enforse:
        app.add_middleware(UserAgentMiddleware)
    if not disable_logger:
        app.add_middleware(RequestResponseLoggerMiddleware)

    app.include_router(info_router)
    create_scalar_doc(app)
    return app


def get_workers_count() -> int:
    """Calculate optimal number of worker processes."""
    cores = multiprocessing.cpu_count()
    # Use (2 * cores + 1) for CPU-bound applications
    # Use (cores * 2) for IO-bound applications (like most web apps)
    return cores * 2


def run_server(
    app: FastAPIFoundation,
    app_path: str,
    host: str = "0.0.0.0",
    port: int = 8000,
    environment: str = "production",
    debug: bool = False,
    # Max concurrent connections (adjust based on resources)
    limit_concurrency: int = 100,
    backlog: int = 2048,  # Maximum number of pending connections
    timeout_keep_alive: int = 30
):
    """
    Run the FastAPI server with optimized settings for production.

    Args:
        app: The FastAPI application instance
        app_path: Path to the FastAPI application
        host: Host address to bind to
        port: Port to bind to
        environment: Environment name (production, development, etc.)
        debug: Enable debug mode
    """
    workers = get_workers_count() if not debug else 1

    config = {
        # Core settings
        "app": app_path,
        "host": host,
        "port": port,
        "workers": workers,

        # Performance settings
        "loop": "uvloop",  # High-performance event loop
        "http": "httptools",  # Fast HTTP protocol implementation
        # Max concurrent connections (adjust based on resources)
        "limit_concurrency": limit_concurrency,
        "backlog": backlog,  # Maximum number of pending connections
        "timeout_keep_alive": timeout_keep_alive,  # Timeout for keep-alive connections

        # Resource settings
        # "worker_class": "uvicorn.workers.UvicornWorker",
        # Trust proxy headers (if behind a reverse proxy)
        "proxy_headers": True,

        "access_log": True,
        "log_level": "info",

        # Development settings
        "reload": debug,
        "reload_delay": 0.25 if debug else 0,
        "reload_excludes": [
            "logs/*",
            "*.log",
            "__pycache__/*",
            "*.pyc",
            ".git/*",           # Git repository files
            "static/*",         # Static assets that change frequently but don't affect app logic
            "tests/*",          # Test files that don't need to trigger reloads
            "data/*",           # Data files that might change but don't affect code
            ".venv/*",           # Virtual environment directory
            "db/*",                  # Another common MongoDB directory
            ".mongodb/*"             # MongoDB temp directories
        ],
    }

    app.logger.info(f"Starting uvicorn server in {environment} mode...")
    app.logger.info(f"Workers: {workers}")
    app.logger.info(f"Host: {host}")
    app.logger.info(f"Port: {port}")

    logging.getLogger('watchfiles').setLevel(logging.DEBUG)

    uvicorn.run(**config)
