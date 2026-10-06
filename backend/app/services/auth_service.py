from __future__ import annotations

import hmac
import re
import secrets
from datetime import datetime, timedelta
from urllib.parse import quote

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import get_settings
from app.contracts.enums import EventType, NotificationDeliveryKind
from app.contracts.errors import AuthenticationError, ValidationError
from app.models.auth_token import MagicLinkToken, UserSession
from app.models.user import User
from app.services.event_service import event_service
from app.services.notification_delivery_service import EmailMessage, notification_delivery_service
from app.utils.datetime import coerce_utc, utcnow

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AuthService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def normalize_email(self, email: str) -> str:
        normalized = email.strip().lower()
        if len(normalized) > 320 or not EMAIL_RE.match(normalized):
            raise ValidationError("Invalid email address")
        return normalized

    def _hash_token(self, token: str) -> str:
        return hmac.new(
            self.settings.app_secret_key.encode("utf-8"),
            token.encode("utf-8"),
            digestmod="sha256",
        ).hexdigest()

    def issue_magic_link(self, db: Session, email: str) -> None:
        normalized = self.normalize_email(email)
        now = utcnow()
        expires_at = now + timedelta(minutes=self.settings.magic_link_ttl_minutes)

        db.execute(
            update(MagicLinkToken)
            .where(MagicLinkToken.email == normalized, MagicLinkToken.consumed_at.is_(None))
            .values(consumed_at=now)
        )

        raw_token = secrets.token_urlsafe(32)
        token = MagicLinkToken(
            email=normalized,
            token_hash=self._hash_token(raw_token),
            expires_at=expires_at,
        )
        db.add(token)
        db.flush()
        event_service.record(
            db,
            event_type=EventType.AUTH_MAGIC_LINK_REQUESTED,
            entity_type="magic_link",
            user_id=None,
            entity_id=str(token.id),
            payload={"email": normalized},
        )

        verify_url = (
            f"{self.settings.app_base_url.rstrip('/')}/#/verify?email={quote(normalized)}&token={quote(raw_token)}"
        )
        body = (
            "Your Follow-Up Radar sign-in link\n\n"
            f"Open this URL to sign in:\n{verify_url}\n\n"
            f"Or use this token manually:\n{raw_token}\n\n"
            f"This link expires at {expires_at.isoformat()}\n"
        )
        message = EmailMessage(
            kind=NotificationDeliveryKind.MAGIC_LINK_EMAIL,
            idempotency_key=f"magic_link:{token.id}",
            to_email=normalized,
            subject="Follow-Up Radar sign-in link",
            body_text=body,
            related_entity_type="magic_link",
            related_entity_id=str(token.id),
            user_id=None,
        )
        notification_delivery_service.ensure_message_shape(
            to_email=message.to_email,
            subject=message.subject,
            body_text=message.body_text,
        )
        delivery = notification_delivery_service.prepare(
            db,
            message=message,
            provider_name=self.settings.email_delivery_mode.value,
        )
        notification_delivery_service.dispatch_delivery(delivery=delivery)
        if delivery.status != "sent":
            db.rollback()
            raise AuthenticationError("Magic link could not be delivered")
        event_service.record(
            db,
            event_type=EventType.AUTH_MAGIC_LINK_DELIVERED,
            entity_type="magic_link",
            user_id=None,
            entity_id=str(token.id),
            payload={"email": normalized, "delivery_id": str(delivery.id)},
        )
        db.commit()

    def verify_magic_link(self, db: Session, email: str, token: str) -> tuple[User, str, datetime]:
        normalized = self.normalize_email(email)
        now = utcnow()
        hashed = self._hash_token(token)
        magic_link = db.execute(
            select(MagicLinkToken).where(
                MagicLinkToken.email == normalized,
                MagicLinkToken.token_hash == hashed,
                MagicLinkToken.consumed_at.is_(None),
            )
        ).scalar_one_or_none()

        if magic_link is None:
            raise AuthenticationError("Magic link token is invalid")
        if coerce_utc(magic_link.expires_at) <= now:
            raise AuthenticationError("Magic link token has expired")

        user = db.execute(select(User).where(User.email == normalized)).scalar_one_or_none()
        if user is None:
            user = User(email=normalized)
            db.add(user)
            db.flush()

        magic_link.consumed_at = now

        session_token_raw = secrets.token_urlsafe(48)
        session_expires_at = now + timedelta(days=self.settings.session_ttl_days)
        user_session = UserSession(
            user_id=user.id,
            token_hash=self._hash_token(session_token_raw),
            expires_at=session_expires_at,
        )
        db.add(user_session)
        db.flush()
        event_service.record(
            db,
            event_type=EventType.AUTH_LOGIN_SUCCESS,
            entity_type="user_session",
            user_id=user.id,
            entity_id=str(user_session.id),
            payload={"email": normalized},
        )
        db.commit()
        return user, session_token_raw, session_expires_at

    def authenticate_bearer(self, db: Session, raw_bearer_token: str) -> User:
        if not raw_bearer_token or not raw_bearer_token.strip():
            raise AuthenticationError("Missing bearer token")
        token_hash = self._hash_token(raw_bearer_token.strip())
        now = utcnow()
        session = db.execute(
            select(UserSession).where(
                UserSession.token_hash == token_hash,
                UserSession.revoked_at.is_(None),
            )
        ).scalar_one_or_none()
        if session is None:
            raise AuthenticationError("Invalid session token")
        if coerce_utc(session.expires_at) <= now:
            raise AuthenticationError("Session token has expired")

        user = db.execute(select(User).where(User.id == session.user_id)).scalar_one_or_none()
        if user is None:
            raise AuthenticationError("Session references missing user")

        session.last_seen_at = now
        db.commit()
        return user


auth_service = AuthService()
