from app.schemas.auth import (
    AuthTokenResponse,
    CurrentUserResponse,
    RequestMagicLinkRequest,
    RequestMagicLinkResponse,
    VerifyMagicLinkRequest,
)
from app.schemas.followup_item import (
    FollowUpItemCompleteRequest,
    FollowUpItemCreate,
    FollowUpItemRead,
    FollowUpItemRescheduleRequest,
    FollowUpItemUpdate,
)

__all__ = [
    "AuthTokenResponse",
    "CurrentUserResponse",
    "RequestMagicLinkRequest",
    "RequestMagicLinkResponse",
    "VerifyMagicLinkRequest",
    "FollowUpItemCompleteRequest",
    "FollowUpItemCreate",
    "FollowUpItemRead",
    "FollowUpItemRescheduleRequest",
    "FollowUpItemUpdate",
]
