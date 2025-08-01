import langfuse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class LangfuseMiddleware(BaseHTTPMiddleware):
    """FastAPI/Starlette middleware that creates a Langfuse span for each HTTP request."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        lf_client = langfuse.get_client()  # type: ignore[attr-defined]
        span_name = f"{request.method} {request.url.path}"

        # Create span; all downstream LLM traces will be nested automatically
        with lf_client.start_as_current_span(  # type: ignore[attr-defined]
            name=span_name,
            metadata={"path": str(request.url.path), "method": request.method},
        ):
            response: Response = await call_next(request)
        return response 