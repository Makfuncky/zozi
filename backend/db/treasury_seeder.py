"""GCC Chart of Accounts and Treasury System Seeding for ZOZI."""
from __future__ import annotations

import logging
from decimal import Decimal

from sqlalchemy.orm import Session

from data.models import Account, AccountGroup, TreasuryAccount

logger = logging.getLogger(__name__)


CHART_OF_ACCOUNTS = {
    "asset": [
        {"code": "1010", "name": "Cash in Operating Account", "normal_side": "debit", "currency": "USD"},
        {"code": "1020", "name": "Cash in Gateway Settlement Account", "normal_side": "debit", "currency": "USD"},
        {"code": "1030", "name": "Accounts Receivable - Customers", "normal_side": "debit", "currency": "USD"},
        {"code": "1040", "name": "Inventory Assets", "normal_side": "debit", "currency": "USD"},
        {"code": "1050", "name": "Prepaid Expenses", "normal_side": "debit", "currency": "USD"},
        {"code": "1060", "name": "Fixed Assets - Equipment", "normal_side": "debit", "currency": "USD"},
    ],
    "liability": [
        {"code": "2010", "name": "Accounts Payable - Suppliers", "normal_side": "credit", "currency": "USD"},
        {"code": "2020", "name": "Accounts Payable - Logistics", "normal_side": "credit", "currency": "USD"},
        {"code": "2030", "name": "Output VAT Payable", "normal_side": "credit", "currency": "USD"},
        {"code": "2031", "name": "Input VAT Payable", "normal_side": "credit", "currency": "USD"},
        {"code": "2040", "name": "Accrued Salaries Payable", "normal_side": "credit", "currency": "USD"},
        {"code": "2050", "name": "Accrued Commission Payable", "normal_side": "credit", "currency": "USD"},
        {"code": "2060", "name": "Customer Refund Liability", "normal_side": "credit", "currency": "USD"},
        {"code": "2070", "name": "EOSB Payable - Employees", "normal_side": "credit", "currency": "USD"},
    ],
    "equity": [
        {"code": "3010", "name": "Retained Earnings", "normal_side": "credit", "currency": "USD"},
        {"code": "3020", "name": "Owner Equity - Founders", "normal_side": "credit", "currency": "USD"},
    ],
    "revenue": [
        {"code": "4010", "name": "Product Sales Revenue", "normal_side": "credit", "currency": "USD"},
        {"code": "4020", "name": "Service Fee Revenue", "normal_side": "credit", "currency": "USD"},
        {"code": "4030", "name": "Logistics Service Revenue", "normal_side": "credit", "currency": "USD"},
        {"code": "4040", "name": "Subscription Revenue", "normal_side": "credit", "currency": "USD"},
    ],
    "cogs": [
        {"code": "5010", "name": "Cost of Goods Sold - Products", "normal_side": "debit", "currency": "USD"},
        {"code": "5020", "name": "Cost of Goods Sold - Logistics", "normal_side": "debit", "currency": "USD"},
    ],
    "expense": [
        {"code": "6010", "name": "Operating Expenses - Marketing", "normal_side": "debit", "currency": "USD"},
        {"code": "6020", "name": "Operating Expenses - Technology", "normal_side": "debit", "currency": "USD"},
        {"code": "6030", "name": "Operating Expenses - Admin", "normal_side": "debit", "currency": "USD"},
        {"code": "6040", "name": "Operating Expenses - Salaries", "normal_side": "debit", "currency": "USD"},
        {"code": "6050", "name": "Operating Expenses - Professional Services", "normal_side": "debit", "currency": "USD"},
    ],
}

TREASURY_BUCKETS = [
    {"slug": "operating_cash", "name": "Operating Cash", "account_type": "operating", "currency": "USD"},
    {"slug": "gateway_settlement", "name": "Gateway Settlement", "account_type": "settlement", "currency": "USD"},
    {"slug": "supplier_reserve", "name": "Supplier Reserve", "account_type": "reserve", "currency": "USD"},
    {"slug": "logistics_reserve", "name": "Logistics Reserve", "account_type": "reserve", "currency": "USD"},
    {"slug": "vat_reserve", "name": "VAT Reserve", "account_type": "tax", "currency": "USD"},
    {"slug": "eosb_reserve", "name": "EOSB Reserve", "account_type": "liability", "currency": "USD"},
]


def _get_or_create_account_group(
    db: Session,
    code: str,
    name: str,
    account_type: str,
    normal_side: str,
    display_order: int,
) -> AccountGroup:
    group = db.query(AccountGroup).filter(AccountGroup.code == code).first()
    if group:
        return group
    group = AccountGroup(
        code=code,
        name=name,
        account_type=account_type,
        normal_side=normal_side,
        display_order=display_order,
        country_code="OM",
    )
    db.add(group)
    db.flush()
    logger.info("Created account group: %s", code)
    return group


def seed_account_groups(db: Session) -> None:
    groups = [
        ("ASSET", "Asset Accounts", "asset", "debit", 1),
        ("LIABILITY", "Liability Accounts", "liability", "credit", 2),
        ("EQUITY", "Equity Accounts", "equity", "credit", 3),
        ("REVENUE", "Revenue Accounts", "revenue", "credit", 4),
        ("COGS", "Cost of Goods Sold", "expense", "debit", 5),
        ("EXPENSE", "Expense Accounts", "expense", "debit", 6),
    ]
    for code, name, account_type, normal_side, display_order in groups:
        _get_or_create_account_group(db, code, name, account_type, normal_side, display_order)
    db.commit()
    logger.info("Account groups seeded successfully")


def seed_chart_of_accounts(db: Session) -> None:
    seed_account_groups(db)
    for category, accounts in CHART_OF_ACCOUNTS.items():
        for acc in accounts:
            existing = db.query(Account).filter(Account.code == acc["code"]).first()
            if existing:
                continue
            group_code = category.upper()
            group = db.query(AccountGroup).filter(AccountGroup.code == group_code).first()
            if not group:
                logger.warning("Account group %s not found for account %s", category, acc["code"])
                continue
            account = Account(
                group_id=group.id,
                code=acc["code"],
                name=acc["name"],
                normal_side=acc["normal_side"],
                currency=acc.get("currency", "USD"),
                country_code="OM",
                is_active=True,
                display_order=len(db.query(Account).filter(Account.group_id == group.id).all()) + 1,
            )
            db.add(account)
            logger.info("Created account: %s - %s", acc["code"], acc["name"])
    db.commit()
    logger.info("Chart of accounts seeded successfully")


def seed_treasury_buckets(db: Session) -> None:
    for bucket in TREASURY_BUCKETS:
        existing = db.query(TreasuryAccount).filter(TreasuryAccount.slug == bucket["slug"]).first()
        if existing:
            continue
        account = TreasuryAccount(
            slug=bucket["slug"],
            name=bucket["name"],
            account_type=bucket["account_type"],
            currency=bucket.get("currency", "USD"),
            gl_account_code=bucket["slug"].upper(),
            description=bucket["name"],
            is_active=True,
        )
        db.add(account)
        logger.info("Created treasury bucket: %s", bucket["slug"])
    db.commit()
    logger.info("Treasury buckets seeded successfully")


def seed_treasury_system(db: Session) -> None:
    seed_chart_of_accounts(db)
    seed_treasury_buckets(db)
    logger.info("Treasury system seeded successfully")


if __name__ == "__main__":
    from db.database import SessionLocal
    db = SessionLocal()
    try:
        seed_treasury_system(db)
    finally:
        db.close()

