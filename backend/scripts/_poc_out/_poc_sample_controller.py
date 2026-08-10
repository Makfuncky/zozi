"""AUTO-GENERATED router for controllers._poc_sample_controller. Do not edit by hand."""
from fastapi import APIRouter, Depends
from controllers._poc_sample_controller import CouponOut, _require_admin, create_coupon_by_country, list_coupons_by_country

router = APIRouter(prefix='/api/v1/promotions')

router.add_api_route(
    '/{code}/coupons',
    list_coupons_by_country,
    methods=['GET'],
    response_model=None,
    status_code=200,
    dependencies=[Depends(_require_admin)],
    tags=['promotions'],
)

router.add_api_route(
    '/{code}/coupons',
    create_coupon_by_country,
    methods=['POST'],
    response_model=CouponOut,
    status_code=201,
    dependencies=[Depends(_require_admin)],
    tags=['promotions'],
)
