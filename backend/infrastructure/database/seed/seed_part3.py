import json
import logging
import os
import re
import warnings
from decimal import Decimal
from typing import Any, Callable

from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from infrastructure.database.database import engine
from domains.governance.models.user import User
from domains.catalog.models.products import Category
from domains.catalog.models.products import Product
from domains.comms.models.marketing import EmailTemplate
from domains.comms.models.suppliers import SupplierProfile
from domains.country.models.countries import CountryConfig
from domains.logistics.models.logistics import LogisticsPartner
from domains.logistics.models.logistics import LogisticsPartnerServiceArea
from domains.logistics.models.logistics import LogisticsPricingProfile
from domains.logistics.models.logistics import LogisticsVehicleRule
from domains.logistics.models.logistics import Shipment
from domains.logistics.models.logistics import ShipmentEvent
from domains.orders.models.orders import Order
from domains.orders.models.orders import OrderItem
from domains.orders.models.orders import OrderLogisticsAllocation
from domains.hr.models.employee_models import (
def _seed_countries(db: Session) -> None:
    logger.info("Seeding countries...")
    from domains.country.models.countries import CountryConfig
    
    existing_count = db.query(CountryConfig).count()
    if existing_count > 0:
        logger.info(f"Countries already exist ({existing_count}), skipping")
        return
    
    demo_countries = [
        {
            "code": "AE",
            "name": "United Arab Emirates",
            "currency": "AED",
            "timezone": "Asia/Dubai",
            "currency_symbol": "د.إ",
            "phone_code": "+971",
            "language": "en",
            "is_active": True,
            "tax_type": "VAT",
            "tax_rate": Decimal("0.05"),
            "tax_name": "VAT",
            "tax_inclusive": False,
        },
        {
            "code": "SA",
            "name": "Saudi Arabia",
            "currency": "SAR",
            "timezone": "Asia/Riyadh",
            "currency_symbol": "﷼",
            "phone_code": "+966",
            "language": "ar",
            "is_active": True,
            "tax_type": "VAT",
            "tax_rate": Decimal("0.15"),
            "tax_name": "VAT",
            "tax_inclusive": False,
        },
        {
            "code": "IN",
            "name": "India",
            "currency": "INR",
            "timezone": "Asia/Kolkata",
            "currency_symbol": "₹",
            "phone_code": "+91",
            "language": "en",
            "is_active": True,
            "tax_type": "GST",
            "tax_rate": Decimal("0.18"),
            "tax_name": "GST",
            "tax_inclusive": False,
        },
    ]
    
    for c in demo_countries:
        country = CountryConfig(**c)
        db.add(country)
        logger.info(f"Seeded country: {c['code']} - {c['name']}")
    
    db.commit()


def _seed_employee_data(db: Session) -> None:
    logger.info("Seeding employee data...")
    
    from infrastructure.utils.rls_interceptor import set_rls_context
    set_rls_context(None, is_restricted=False)
    
    countries = db.query(CountryConfig).all()
    if not countries:
        logger.warning("No countries found, skipping employee seeding")
        return
    
    existing_count = db.query(Employee).count()
    if existing_count > 0:
        logger.info(f"Employees already exist ({existing_count}), skipping")
        return
    
    admin = db.query(User).filter(User.role == "admin").first()
    if not admin:
        admin = _ensure_demo_user(
            db,
            email="admin@zozi.com",
            username="admin",
            password=_seed_password("SEED_ADMIN_PASSWORD"),
            role="admin",
            log_label="admin"
        )
    
    for country in countries[:3]:
        office = Office(
            name=f"{country.name} Office",
            country_code=country.code,
            city=country.name,
            latitude=25.0,
            longitude=45.0
        )
        db.add(office)
    
    db.commit()
    
    for i, country in enumerate(countries[:5]):
        office = db.query(Office).filter(Office.country_code == country.code).first()
        user = User(
            email=f"employee{i}@zozi.com",
            username=f"employee{i}",
            hashed_password=get_password_hash(_seed_password("SEED_EMPLOYEE_PASSWORD")),
            role="employee",
            full_name=f"Employee {i}",
            country_code=country.code,
        )
        db.add(user)
        db.commit()
        
        emp = Employee(
            user_id=user.id,
            employee_code=f"EMP{i:04d}",
            office_id=office.id if office else None,
            department="Operations",
            position="Staff",
            employment_type="full_time",
            employment_status="active",
            salary=Decimal("500.000"),
            currency="OMR",
            country_code=country.code,
            hire_date=_utcnow(),
            gender="male",
        )
        db.add(emp)
    
    db.commit()
    logger.info("Employee data seeded successfully")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_data(db)
        _seed_employee_data(db)
    finally:
        db.close()



