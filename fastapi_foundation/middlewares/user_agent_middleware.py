
from fastapi_foundation.models.user_agent_params import UserAgentParams
from typing import Literal, Optional, Callable
from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, ValidationError
from starlette.responses import Response, JSONResponse
import logging
import json

logger = logging.getLogger("")


class UserAgentMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: FastAPI,
        user_agent_header: str = "user-agent",
        user_agent_prefix: str = 'cross_connect'
    ):
        """
        Middleware to parse User-Agent header in the format:
        "cross_connect/app_version/version_code/platform/os_version/device_id/device_model"

        Args:
            app: FastAPI application
            user_agent_header: The header name that contains the User-Agent string (default: "user-agent")
        """
        super().__init__(app)
        self.user_agent_header = user_agent_header
        self.user_agent_prefix = user_agent_prefix

    async def dispatch(self, request: Request, call_next):
        # Extract the User-Agent header
        user_agent = request.headers.get(self.user_agent_header)

        # Add a default None value to the request state
        request.state.user_agent_params = None

        if (request.url.path == "/health" or
                request.url.path.startswith("/docs") or
                request.url.path.startswith("/openapi.json")
                ):
            return await call_next(request)

        if user_agent:
            try:
                # Parse the User-Agent string
                request.state.user_agent_params = self._parse_user_agent(
                    user_agent)
                # logger.info(json.dumps(request.state.user_agent_params.dict()))
            except Exception as e:
                logger.warning(
                    f"Failed to parse User-Agent: {user_agent}. Error: {str(e)}")
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid User-Agent format"}
                )
        else:
            logger.warning(
                f"User-Agent header not found in request: {request.url}")
            return JSONResponse(
                status_code=400,
                content={"detail": "User-Agent header is required"}
            )

        # Continue processing the request
        response = await call_next(request)
        return response

    def _parse_user_agent(self, user_agent_string: str) -> UserAgentParams:
        """

        "cross_connect/app_version/version_code/platform/os_version/device_id/device_model"
        Parse a user agent string into a UserAgentParams object.

        Args:
            user_agent_string: String in the specified format

        Returns:
            UserAgentParams object with extracted fields

        Raises:
            ValueError: If the string format is invalid or missing required fields
        """
        parts = user_agent_string.split('/')

        if len(parts) != 7:
            raise ValueError(
                f"Expected 7 parts in user agent string, got {len(parts)}")

        # Check if the string starts with the expected prefix

        if parts[0] != self.user_agent_prefix:
            raise ValueError(
                f"User-Agent string must start with '{self.user_agent_prefix}'")

        # Convert version_code to integer
        try:
            version_code = int(parts[2])
        except ValueError:
            raise ValueError(
                f"version_code must be an integer, got: {parts[2]}")

        # Validate platform
        if parts[3] not in ["android", "ios"]:
            raise ValueError(
                f"platform must be 'android' or 'ios', got: {parts[3]}")

        return UserAgentParams(
            app_version=parts[1],
            version_code=version_code,
            platform=parts[3],
            os_version=parts[4],
            device_id=parts[5],
            device_model=parts[6]
        )
