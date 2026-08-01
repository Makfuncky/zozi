from fastapi import APIRouter, Depends, HTTPException, Query

from dependencies.auth import get_current_user
from utils.currency import convert_between_currencies, currency_for_country, get_currency_context, normalize_currency_code, refresh_rate_cache

router = APIRouter()


@router.get("/context")
def currency_context(
    country: str | None = Query(default=None, max_length=5),
    currency: str | None = Query(default=None, max_length=5),
):
    return get_currency_context(country=country, currency=currency, default_currency="OMR")


@router.get("/rates")
def currency_rates(
    amount: float = Query(default=1.0, gt=0),
    base: str = Query(default="AED", max_length=5),
    target: str | None = Query(default=None, max_length=5),
    country: str | None = Query(default=None, max_length=5),
):
    resolved_target = normalize_currency_code(target, default="") if target else currency_for_country(country, default_currency="OMR")
    converted, rate, source = convert_between_currencies(amount, base, resolved_target)
    return {
        "amount": amount,
        "base_currency": normalize_currency_code(base),
        "target_currency": resolved_target,
        "country": country,
        "converted_amount": float(converted),
        "rate": float(rate),
        "source": source,
    }


@router.post("/rates/refresh")
def refresh_currency_rates(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") not in ("admin", "sub_admin", "moderator"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return refresh_rate_cache()

