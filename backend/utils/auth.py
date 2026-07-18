"""Authentication helpers with Redis-backed and in-memory fallbacks."""
from __future__ import annotations

import logging
import re
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
from fastapi import HTTPException, status
from jose import JWTError, jwt

from utils.config import settings


logger = logging.getLogger(__name__)

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = int(settings.access_token_expire_minutes)
REFRESH_TOKEN_EXPIRE_DAYS = int(settings.refresh_token_expire_days)
LOGIN_FAIL_MAX = 5
LOGIN_LOCKOUT_TTL = 900

_memory_blacklist: dict[str, float] = {}
_memory_failed_logins: dict[str, tuple[int, float]] = {}
_redis_client = None


def _coerce_failed_login_entry(entry: object, *, now: float) -> tuple[int, float]:
    if isinstance(entry, tuple) and len(entry) == 2:
        try:
            count = int(entry[0])
        except Exception:
            count = 0
        try:
            expiry = float(entry[1])
        except Exception:
            expiry = now + LOGIN_LOCKOUT_TTL
        return count, expiry
    if isinstance(entry, int):
        return int(entry), now + LOGIN_LOCKOUT_TTL
    return 0, now + LOGIN_LOCKOUT_TTL


def _get_redis():
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    try:
        import redis as redis_module

        client = redis_module.from_url(
            settings.redis_url,
            socket_connect_timeout=1,
            socket_timeout=1,
            decode_responses=True,
        )
        _redis_client = client
        return client
    except Exception:
        return None


def get_redis_health_status() -> dict[str, object]:
    client = _get_redis()
    return {
        "available": client is not None,
        "shared_state": client is not None,
        "backend": "redis" if client is not None else "memory_fallback",
        "configured": bool(str(settings.redis_url).strip()),
    }


def _prune_memory_blacklist() -> None:
    now = time.monotonic()
    for key, expiry in list(_memory_blacklist.items()):
        if expiry <= now:
            _memory_blacklist.pop(key, None)


def blacklist_token(jti: str, ttl_seconds: int) -> None:
    client = _get_redis()
    if client is not None:
        try:
            client.setex(f"bl:{jti}", ttl_seconds, "1")
            return
        except Exception:
            pass

    _memory_blacklist[jti] = time.monotonic() + ttl_seconds
    _prune_memory_blacklist()


def is_token_blacklisted(jti: str) -> bool:
    client = _get_redis()
    if client is not None:
        try:
            return client.exists(f"bl:{jti}") == 1
        except Exception:
            pass

    expiry = _memory_blacklist.get(jti)
    if expiry is None:
        return False
    if time.monotonic() >= expiry:
        _memory_blacklist.pop(jti, None)
        return False
    return True


def record_failed_login(identifier: str) -> int:
    client = _get_redis()
    key = f"fl:{identifier}"
    if client is not None:
        try:
            count = int(client.incr(key))
            if count == 1:
                client.expire(key, LOGIN_LOCKOUT_TTL)
            return count
        except Exception:
            pass

    now = time.monotonic()
    count, expiry = _coerce_failed_login_entry(
        _memory_failed_logins.get(identifier),
        now=now,
    )
    if now >= expiry:
        count = 0
        expiry = now + LOGIN_LOCKOUT_TTL
    count += 1
    _memory_failed_logins[identifier] = (count, expiry)
    return count


def is_account_locked(identifier: str) -> bool:
    client = _get_redis()
    key = f"fl:{identifier}"
    if client is not None:
        try:
            raw = client.get(key)
            return raw is not None and int(raw) >= LOGIN_FAIL_MAX
        except Exception:
            pass

    entry = _memory_failed_logins.get(identifier)
    if entry is None:
        return False
    count, expiry = _coerce_failed_login_entry(entry, now=time.monotonic())
    _memory_failed_logins[identifier] = (count, expiry)
    if time.monotonic() >= expiry:
        _memory_failed_logins.pop(identifier, None)
        return False
    return count >= LOGIN_FAIL_MAX


def clear_failed_logins(identifier: str) -> None:
    client = _get_redis()
    key = f"fl:{identifier}"
    if client is not None:
        try:
            client.delete(key)
            return
        except Exception:
            pass
    _memory_failed_logins.pop(identifier, None)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    if len(password) > 72:
        password = password[:72]
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None, device_fp: str | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc).replace(tzinfo=None) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access", "jti": uuid.uuid4().hex})
    if device_fp:
        to_encode["dfp"] = device_fp
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict[str, Any], family_id: str | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "jti": uuid.uuid4().hex,
        "family_id": family_id or uuid.uuid4().hex,
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


REFRESH_TOKEN_USED_TTL = REFRESH_TOKEN_EXPIRE_DAYS * 86400 + 3600
ADMIN_2FA_VERIFY_TTL = 900  # 15 minutes


def mark_refresh_token_used(family_id: str, jti: str) -> None:
    """Mark a specific refresh JTI as used (reuse = family compromised)."""
    client = _get_redis()
    if client is not None:
        try:
            client.setex(f"rtu:{family_id}:{jti}", REFRESH_TOKEN_USED_TTL, "1")
            return
        except Exception:
            pass
    _memory_blacklist[f"rtu:{family_id}:{jti}"] = time.monotonic() + REFRESH_TOKEN_USED_TTL


def is_refresh_token_used(family_id: str, jti: str) -> bool:
    """Check if this refresh JTI was already consumed (replay detected)."""
    client = _get_redis()
    if client is not None:
        try:
            return client.exists(f"rtu:{family_id}:{jti}") == 1
        except Exception:
            pass
    expiry = _memory_blacklist.get(f"rtu:{family_id}:{jti}")
    if expiry is None:
        return False
    if time.monotonic() >= expiry:
        _memory_blacklist.pop(f"rtu:{family_id}:{jti}", None)
        return False
    return True


def revoke_refresh_family(family_id: str) -> None:
    """Revoke an entire refresh token family (after reuse detection)."""
    client = _get_redis()
    if client is not None:
        try:
            client.setex(f"rtf:{family_id}", REFRESH_TOKEN_USED_TTL, "1")
            return
        except Exception:
            pass
    _memory_blacklist[f"rtf:{family_id}"] = time.monotonic() + REFRESH_TOKEN_USED_TTL


def is_refresh_family_revoked(family_id: str) -> bool:
    """Check if a refresh token family has been revoked."""
    client = _get_redis()
    if client is not None:
        try:
            return client.exists(f"rtf:{family_id}") == 1
        except Exception:
            pass
    expiry = _memory_blacklist.get(f"rtf:{family_id}")
    if expiry is None:
        return False
    if time.monotonic() >= expiry:
        _memory_blacklist.pop(f"rtf:{family_id}", None)
        return False
    return True


TEMP_TOKEN_EXPIRE_MINUTES = 5


def create_temp_token(data: dict[str, Any]) -> str:
    """Short-lived JWT used as a temporary challenge token for 2FA."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=TEMP_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "temp", "jti": uuid.uuid4().hex})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_temp_token(token: str) -> dict[str, Any]:
    """Verify a short-lived temp token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if payload.get("type") != "temp":
        raise HTTPException(status_code=401, detail="Invalid token type")
    return payload


PASSWORD_COMPLEXITY_RE = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{}|;':\",./<>?]).{8,}$"
)

def validate_password_complexity(password: str) -> None:
    if not PASSWORD_COMPLEXITY_RE.match(password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters with at least one uppercase letter, "
            "one lowercase letter, one digit, and one special character",
        )


def _decode_and_validate(token: str, token_type: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    if payload.get("type") != token_type:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    jti = str(payload.get("jti", ""))
    if jti and is_token_blacklisted(jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
    return payload


def verify_token(token: str) -> str:
    payload = _decode_and_validate(token, "access")
    subject = payload.get("sub")
    if subject is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return str(subject)


def verify_refresh_token(token: str) -> str:
    payload = _decode_and_validate(token, "refresh")
    subject = payload.get("sub")
    if subject is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return str(subject)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


hash_password = get_password_hash


__all__ = [
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "REFRESH_TOKEN_EXPIRE_DAYS",
    "LOGIN_FAIL_MAX",
    "LOGIN_LOCKOUT_TTL",
    "_get_redis",
    "_memory_blacklist",
    "_memory_failed_logins",
    "blacklist_token",
    "clear_failed_logins",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "get_password_hash",
    "get_redis_health_status",
    "hash_password",
    "is_account_locked",
    "is_token_blacklisted",
    "record_failed_login",
    "verify_password",
    "verify_refresh_token",
    "verify_token",
]

