from domains.finance.services.payments.payment_engine import (
    _paypal_breaker,
    _paytabs_breaker,
    _stripe_breaker,
    _tap_breaker,
    _thawani_breaker,
)


def test_provider_specific_thresholds():
    assert _stripe_breaker.failure_threshold == 5
    assert _stripe_breaker.recovery_timeout == 30.0

    assert _tap_breaker.failure_threshold == 3
    assert _tap_breaker.recovery_timeout == 20.0

    assert _paytabs_breaker.failure_threshold == 4
    assert _paytabs_breaker.recovery_timeout == 25.0

    assert _thawani_breaker.failure_threshold == 3
    assert _thawani_breaker.recovery_timeout == 20.0

    assert _paypal_breaker.failure_threshold == 4
    assert _paypal_breaker.recovery_timeout == 30.0
