from datetime import datetime, timedelta, timezone
from typing import Optional
import logging
import bcrypt
from jose import JWTError, jwt
from fastapi import HTTPException, status
from utils.config import settings

logger = logging.getLogger(__name__)

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = settings.refresh_token_expire_days

# ── Redis blacklist (falls back to in-memory set when Redis is unavailable) ───

_memory_blacklist: set[str] = set()

def _get_redis():
    """Return a Redis client or None if unavailable."""
    try:
        import redis as _redis
        client = _redis.from_url(settings.redis_url, socket_connect_timeout=1)
        client.ping()
        return client
    except Exception:
        return None


def blacklist_token(jti: str, ttl_seconds: int) -> None:
    """Store jti in Redis (or in-memory fallback)."""
    r = _get_redis()
    if r:
        r.setex(f"bl:{jti}", ttl_seconds, "1")
    else:
        _memory_blacklist.add(jti)
        logger.warning("Redis unavailable — token blacklisted in memory only.")


def is_token_blacklisted(jti: str) -> bool:
    r = _get_redis()
    if r:
        return r.exists(f"bl:{jti}") == 1
    return jti in _memory_blacklist


# ── Password helpers ──────────────────────────────────────────────────────────

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    if len(password) > 72:
        password = password[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


# ── Token creation ────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc).replace(tzinfo=None) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ── Token verification ────────────────────────────────────────────────────────

def verify_token(token: str) -> str:
    """Decode access token → return username.  Raises 401 on any failure."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        jti: str = payload.get("jti", "")
        if jti and is_token_blacklisted(jti):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def verify_refresh_token(token: str) -> str:
    """Decode refresh token → return username.  Raises 401 on any failure."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        jti: str = payload.get("jti", "")
        if jti and is_token_blacklisted(jti):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
