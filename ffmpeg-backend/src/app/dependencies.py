"""FastAPI dependencies for request validation and authentication."""

from typing import Any

from fastapi import Header, HTTPException, Request, status

from app.config import get_settings


async def verify_internal_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
) -> str:
    """Verify internal API key from request header.

    Args:
        x_api_key: API key from X-API-Key header

    Returns:
        str: Validated API key

    Raises:
        HTTPException: If API key is invalid
    """
    settings = get_settings()

    if not settings.internal_api_keys:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal API authentication not configured",
        )

    if x_api_key not in settings.internal_api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "X-API-Key"},
        )

    return x_api_key


async def get_auth_context(request: Request) -> dict[str, Any]:
    """Get authentication context from request state.

    This dependency can be used to access authentication information
    that was set by the InternalAuthMiddleware.

    Args:
        request: FastAPI request with auth state

    Returns:
        dict: Authentication context with method and credentials

    Raises:
        HTTPException: If authentication information is not available
    """
    auth_method = getattr(request.state, "auth_method", None)

    if not auth_method:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    context = {"method": auth_method}

    if auth_method == "api_key":
        context["api_key"] = getattr(request.state, "api_key", None)
    elif auth_method == "jwt":
        context["jwt_payload"] = getattr(request.state, "jwt_payload", None)

    return context


async def require_internal_auth(request: Request) -> dict[str, Any]:
    """Require internal API authentication.

    This is a simple dependency that ensures the request has been
    authenticated by the InternalAuthMiddleware. Use this on endpoints
    that should only be accessible with internal authentication.

    Args:
        request: FastAPI request

    Returns:
        dict: Authentication context

    Raises:
        HTTPException: If not authenticated
    """
    return await get_auth_context(request)
