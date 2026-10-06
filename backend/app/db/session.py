from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
url = make_url(settings.database_url)
connect_args: dict[str, object] = {}
if url.get_backend_name() == "sqlite":
    connect_args["check_same_thread"] = False
engine = create_engine(settings.database_url, pool_pre_ping=True, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, class_=Session, autoflush=False, autocommit=False, expire_on_commit=False)
