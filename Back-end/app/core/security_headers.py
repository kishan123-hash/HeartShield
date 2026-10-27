from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from fastapi import Request, Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Layer 1 Security: Adds mandatory security and browser isolation headers
    to prevent MIME-sniffing, clickjacking, cross-site scripting, and unauthorized frame embedding.
    """

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent Clickjacking / frame embedding
        response.headers["X-Frame-Options"] = "DENY"

        # Enable XSS filtering in browsers
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer privacy protection
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Restrict sensitive browser features
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"

        # HSTS (Strict-Transport-Security) for TLS enforcement
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Standard secure Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data: blob: http: https:; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "connect-src 'self' http://localhost:8000 http://127.0.0.1:8000 http://localhost:5173 http://127.0.0.1:5173; "
            "frame-ancestors 'none';"
        )

        return response
