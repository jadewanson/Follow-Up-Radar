from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from app.contracts.enums import AppEnv, EmailDeliveryMode
from app.contracts.errors import ConfigurationError


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise ConfigurationError(f"Missing required environment variable: {name}")
    return value.strip()


def _parse_int(name: str, default: int | None = None) -> int:
    raw = os.getenv(name)
    if raw is None:
        if default is None:
            raise ConfigurationError(f"Missing required integer environment variable: {name}")
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigurationError(f"Environment variable {name} must be an integer") from exc
    if value <= 0:
        raise ConfigurationError(f"Environment variable {name} must be > 0")
    return value


def _parse_env(name: str, default: AppEnv = AppEnv.DEVELOPMENT) -> AppEnv:
    raw = os.getenv(name, default.value).strip().lower()
    try:
        return AppEnv(raw)
    except ValueError as exc:
        allowed = ", ".join(env.value for env in AppEnv)
        raise ConfigurationError(f"Environment variable {name} must be one of: {allowed}") from exc


def _parse_email_delivery_mode(name: str, default: EmailDeliveryMode) -> EmailDeliveryMode:
    raw = os.getenv(name, default.value).strip().lower()
    try:
        return EmailDeliveryMode(raw)
    except ValueError as exc:
        allowed = ", ".join(mode.value for mode in EmailDeliveryMode)
        raise ConfigurationError(f"Environment variable {name} must be one of: {allowed}") from exc


def _parse_csv(name: str, default: list[str]) -> list[str]:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    values = [item.strip() for item in raw.split(",") if item.strip()]
    if not values:
        raise ConfigurationError(f"Environment variable {name} must contain at least one value")
    return values


def _parse_optional_str(name: str, default: str) -> str:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip()


@dataclass(frozen=True)
class Settings:
    app_env: AppEnv
    app_secret_key: str
    app_base_url: str
    database_url: str
    redis_url: str
    magic_link_ttl_minutes: int
    session_ttl_days: int
    reminder_max_attempts: int
    daily_digest_hour_utc: int
    email_delivery_mode: EmailDeliveryMode
    email_from_address: str
    dev_email_outbox_path: str
    cors_allowed_origins: list[str]
    support_email_address: str
    beta_trial_days: int
    pro_monthly_price_usd: int


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    daily_digest_hour_utc = _parse_int("DAILY_DIGEST_HOUR_UTC", default=7)
    if daily_digest_hour_utc < 0 or daily_digest_hour_utc > 23:
        raise ConfigurationError("Environment variable DAILY_DIGEST_HOUR_UTC must be between 0 and 23")

    email_delivery_mode = _parse_email_delivery_mode("EMAIL_DELIVERY_MODE", default=EmailDeliveryMode.DEV_FILE)
    dev_email_outbox_path = _require_env("DEV_EMAIL_OUTBOX_PATH") if email_delivery_mode == EmailDeliveryMode.DEV_FILE else ""

    return Settings(
        app_env=_parse_env("APP_ENV"),
        app_secret_key=_require_env("APP_SECRET_KEY"),
        app_base_url=_require_env("APP_BASE_URL"),
        database_url=_require_env("DATABASE_URL"),
        redis_url=_require_env("REDIS_URL"),
        magic_link_ttl_minutes=_parse_int("MAGIC_LINK_TTL_MINUTES", default=15),
        session_ttl_days=_parse_int("SESSION_TTL_DAYS", default=30),
        reminder_max_attempts=_parse_int("REMINDER_MAX_ATTEMPTS", default=3),
        daily_digest_hour_utc=daily_digest_hour_utc,
        email_delivery_mode=email_delivery_mode,
        email_from_address=_require_env("EMAIL_FROM_ADDRESS"),
        dev_email_outbox_path=dev_email_outbox_path,
        cors_allowed_origins=_parse_csv("CORS_ALLOWED_ORIGINS", default=["http://localhost:5173"]),
        support_email_address=_parse_optional_str("SUPPORT_EMAIL_ADDRESS", default="support@followup-radar.local"),
        beta_trial_days=_parse_int("BETA_TRIAL_DAYS", default=14),
        pro_monthly_price_usd=_parse_int("PRO_MONTHLY_PRICE_USD", default=9),
    )
