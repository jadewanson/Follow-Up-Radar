from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.api.routes_auth import router as auth_router
from app.api.routes_items import router as items_router
from app.api.routes_billing import router as billing_router
from app.config import get_settings
from app.contracts.errors import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    DomainError,
    NotFoundError,
    StateTransitionError,
    ValidationError,
)

settings = get_settings()

app = FastAPI(title="Follow-Up Radar API", version="0.14.0-iter14")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)
app.include_router(auth_router)
app.include_router(items_router)
app.include_router(billing_router)


@app.exception_handler(DomainError)
def handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
    status_code = status.HTTP_400_BAD_REQUEST
    if isinstance(exc, AuthenticationError):
        status_code = status.HTTP_401_UNAUTHORIZED
    elif isinstance(exc, AuthorizationError):
        status_code = status.HTTP_403_FORBIDDEN
    elif isinstance(exc, NotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, (ValidationError, StateTransitionError, ConfigurationError)):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        },
    )
