"""Recovery script: Rebuilds all corrupted (null-byte) source files."""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(BASE)  # zozi root

def write_file(rel_path, content):
    fp = os.path.join(PROJECT, rel_path)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  RESTORED: {rel_path}")


# ============================================================
# 1. backend/db/database.py
# ============================================================
write_file("backend/db/database.py", '''\
"""Database engine and session factory."""
from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = f"sqlite:///{BASE_DIR / 'zozi.db'}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
''')

# ============================================================
# 2. backend/utils/config.py
# ============================================================
write_file("backend/utils/config.py", '''\
"""Application settings loaded from environment / .env file."""
from __future__ import annotations

import os
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Core ──────────────────────────────────────────────
    APP_NAME: str = "ZOZI Marketplace"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # ── Auth / JWT ────────────────────────────────────────
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ALGORITHM: str = "HS256"

    # ── Database ──────────────────────────────────────────
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'zozi.db'}"

    # ── Stripe ────────────────────────────────────────────
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # ── OpenAI ────────────────────────────────────────────
    OPENAI_API_KEY: str = ""

    # ── Email ─────────────────────────────────────────────
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@zozi.com"

    # ── Uploads ───────────────────────────────────────────
    UPLOAD_DIR: str = str(BASE_DIR / "uploads")
    MAX_UPLOAD_SIZE_MB: int = 10

    # ── Backup ────────────────────────────────────────────
    BACKUP_DIR: str = str(BASE_DIR / "uploads" / "backups")
    MAX_BACKUPS: int = 20

    # ── Encryption ────────────────────────────────────────
    ENCRYPTION_KEY: str = ""


settings = Settings()
''')

# ============================================================
# 3. backend/utils/auth.py
# ============================================================
write_file("backend/utils/auth.py", '''\
"""JWT token utilities."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import jwt
from passlib.context import CryptContext

from utils.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: Dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
''')

# ============================================================
# 4. backend/utils/migrations.py
# ============================================================
write_file("backend/utils/migrations.py", '''\
"""Alembic migration helper."""
from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config


def upgrade_database_to_head() -> None:
    """Run alembic upgrade head programmatically."""
    alembic_ini = str(Path(__file__).resolve().parent.parent / "alembic.ini")
    cfg = Config(alembic_ini)
    command.upgrade(cfg, "head")
''')

# ============================================================
# 5. backend/utils/constants.py
# ============================================================
write_file("backend/utils/constants.py", '''\
"""Application-wide constants."""
from __future__ import annotations

ORDER_STATUSES = [
    "pending", "confirmed", "processing", "shipped", "out_for_delivery",
    "delivered", "cancelled", "returned", "refunded",
]

PAYMENT_STATUSES = ["pending", "paid", "failed", "refunded"]

USER_ROLES = ["customer", "supplier", "admin", "staff", "logistics_partner"]

MODERATION_STATUSES = ["pending", "approved", "rejected"]

RETURN_STATUSES = ["requested", "approved", "rejected", "received", "refunded"]

SHIPMENT_STATUSES = [
    "pending", "picked_up", "in_transit", "out_for_delivery",
    "delivered", "failed", "returned",
]

COUPON_TYPES = ["percentage", "fixed"]

PAYOUT_STATUSES = ["pending", "processing", "completed", "failed"]

ALLOWED_UPLOAD_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif", "application/pdf"]

ALLOWED_UPLOAD_FOLDERS = ["products", "banners", "avatars", "documents", "suppliers"]
''')

print("\\n=== Phase 1 complete: Core utilities restored ===")
