"""Service methods for user write operations."""
from sqlalchemy.orm import Session
from data.models import User, Referral
from data.models import ReferralPointEvent


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def save_user(db: Session, user: User) -> User:
    """Commit and refresh a user object."""
    db.commit()
    db.refresh(user)
    return user


def get_user_by_username(db: Session, username: str) -> User | None:
    """Get user by username."""
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()


def find_user_by_email_or_username(
    db: Session, email: str | None = None, username: str | None = None
) -> User | None:
    """Find a user by email or username (email takes precedence)."""
    if email:
        user = get_user_by_email(db, email)
        if user:
            return user
    if username:
        user = get_user_by_username(db, username)
        if user:
            return user
    return None


def build_user_query(db: Session):
    """Return a base query for paginated user listing."""
    return db.query(User)


def get_or_create_referral(db: Session, user_id: int, code: str) -> Referral:
    """Get a user's referral code row, creating it if missing.

    The ``referrals`` table uses ``referred_id`` as the unique target of a
    referral. For a user's own shareable code we create a self-row whose
    ``referred_id`` equals the user themselves; the generated ``code`` is
    persisted on ``referral_code``.
    """
    existing = (
        db.query(Referral)
        .filter(Referral.referrer_id == user_id)
        .order_by(Referral.id.asc())
        .first()
    )
    if existing:
        if getattr(existing, "referral_code", None) is None:
            existing.referral_code = code
            db.commit()
            db.refresh(existing)
        return existing

    referral = Referral(
        referrer_id=user_id,
        referred_id=user_id,
        referral_code=code,
        status="active",
    )
    db.add(referral)
    db.commit()
    db.refresh(referral)
    return referral


def get_referral_by_referrer_id(db: Session, referrer_id: int) -> list[Referral]:
    """Get referrals by referrer ID."""
    return db.query(Referral).filter(Referral.referrer_id == referrer_id).all()


def update_user_profile(db: Session, user_id: int, **kwargs) -> User | None:
    """Update user profile fields."""
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    for key, value in kwargs.items():
        if hasattr(user, key):
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


def deactivate_user(db: Session, user_id: int) -> bool:
    """Deactivate a user."""
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    user.is_active = False
    db.commit()
    return True
