"""Request ID middleware for FastAPI (Phase 16)."""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import logging

class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware that adds a unique request ID to each request."""

    async def dispatch(self, request: Request, call_next):
        # Allow client to provide request ID, or generate one
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Store in request state for access in routes
        request.state.request_id = request_id
        
        # Setup logging context (simplistic for now, using extra or contextual logging)
        # Note: Standard logging doesn't have built-in easy thread-safe context 
        # without specialized libraries like structlog or contextvars hacks in formatter.
        # Here we just rely on standard logger with filters if applicable.
        
        response: Response = await call_next(request)
        
        # Set in response header for client tracking
        response.headers["X-Request-ID"] = request_id
        return response
