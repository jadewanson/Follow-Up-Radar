from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RequestMagicLinkRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)


class RequestMagicLinkResponse(BaseModel):
    status: str


class VerifyMagicLinkRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    token: str = Field(min_length=32, max_length=512)


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class CurrentUserResponse(BaseModel):
    id: str
    email: str
    timezone: str
    plan: str
    plan_status: str
    created_at: datetime
