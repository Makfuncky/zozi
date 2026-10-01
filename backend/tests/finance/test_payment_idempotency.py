import json

from sqlalchemy.orm import Session

from domains.finance.services.payments.payment_engine import (
    check_payment_idempotency,
    store_payment_idempotency,
)


def test_idempotency_persists_beyond_24h(db_session: Session):
    key = "test_idempotency_persists_24h"
    result = {"status": "completed", "payment_intent_id": "pi_test_123"}

    store_payment_idempotency(key, result, db=db_session)
    db_session.commit()

    cached = check_payment_idempotency(key, db=db_session)
    assert cached is not None
    assert cached["status"] == "completed"
    assert cached["payment_intent_id"] == "pi_test_123"


def test_idempotency_db_fallback_when_redis_miss(db_session: Session):
    key = "test_idempotency_db_fallback"
    result = {"status": "completed", "payment_intent_id": "pi_fallback_456"}

    store_payment_idempotency(key, result, db=db_session)
    db_session.commit()

    cached = check_payment_idempotency(key, db=db_session)
    assert cached is not None
    assert cached["status"] == "completed"
    assert cached["payment_intent_id"] == "pi_fallback_456"


def test_idempotency_returns_none_for_missing_key(db_session: Session):
    cached = check_payment_idempotency("nonexistent_key_99999", db=db_session)
    assert cached is None
