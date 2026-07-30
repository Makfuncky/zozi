"""seed_employee_test_data

Seeds development/test data for the employee management system so that
the frontend Employee page has data to display in development mode.

Revision ID: z2a3b4c5d6e7
Revises: z1a2b3c4d5e6
Create Date: 2026-06-24 18:00:00.000000

"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "z2a3b4c5d6e7"
down_revision: Union[str, Sequence[str], None] = "z1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


OFFICES = {
    "OM": [
        ("Muscat HQ", "Muscat", 23.5880, 58.3829, 500, "Asia/Muscat"),
        ("Salalah Branch", "Salalah", 17.0151, 54.0924, 300, "Asia/Muscat"),
    ],
    "AE": [
        ("Dubai Main Office", "Dubai", 25.2048, 55.2708, 500, "Asia/Dubai"),
        ("Abu Dhabi Branch", "Abu Dhabi", 24.4539, 54.3773, 400, "Asia/Dubai"),
    ],
    "SA": [
        ("Riyadh HQ", "Riyadh", 24.7136, 46.6753, 500, "Asia/Riyadh"),
        ("Jeddah Branch", "Jeddah", 21.4858, 39.1925, 400, "Asia/Riyadh"),
    ],
}

EMPLOYEES = [
    # OM employees
    ("ZOZI-OM-0001", "OM", "Management", "Country Head", "full_time", 4500, "OMR", 0),
    ("ZOZI-OM-0002", "OM", "Finance", "Finance Manager", "full_time", 3500, "OMR", 0),
    ("ZOZI-OM-0003", "OM", "Operations", "Operations Manager", "full_time", 3200, "OMR", 0),
    ("ZOZI-OM-0004", "OM", "Logistics", "Logistics Coordinator", "full_time", 2200, "OMR", 0),
    ("ZOZI-OM-0005", "OM", "Customer Support", "Support Agent", "full_time", 1500, "OMR", 1),
    ("ZOZI-OM-0006", "OM", "Marketing", "Marketing Specialist", "contract", 1800, "OMR", 0),
    # AE employees
    ("ZOZI-AE-0001", "AE", "Management", "Country Head", "full_time", 25000, "AED", 0),
    ("ZOZI-AE-0002", "AE", "Finance", "Finance Manager", "full_time", 20000, "AED", 0),
    ("ZOZI-AE-0003", "AE", "Operations", "Operations Manager", "full_time", 18000, "AED", 0),
    ("ZOZI-AE-0004", "AE", "Logistics", "Senior Logistics Coordinator", "full_time", 15000, "AED", 1),
    ("ZOZI-AE-0005", "AE", "Customer Support", "Team Lead", "full_time", 12000, "AED", 0),
    ("ZOZI-AE-0006", "AE", "Business Development", "BD Manager", "full_time", 22000, "AED", 0),
    # SA employees
    ("ZOZI-SA-0001", "SA", "Management", "Country Head", "full_time", 22000, "SAR", 0),
    ("ZOZI-SA-0002", "SA", "Finance", "Finance Manager", "full_time", 18000, "SAR", 0),
    ("ZOZI-SA-0003", "SA", "Operations", "Operations Manager", "full_time", 16000, "SAR", 0),
    ("ZOZI-SA-0004", "SA", "Logistics", "Logistics Manager", "full_time", 14000, "SAR", 1),
    ("ZOZI-SA-0005", "SA", "Customer Support", "Support Agent", "contract", 8000, "SAR", 0),
    ("ZOZI-SA-0006", "SA", "Compliance", "Compliance Officer", "full_time", 15000, "SAR", 0),
    ("ZOZI-SA-0007", "SA", "Marketing", "Marketing Manager", "full_time", 17000, "SAR", 0),
]


def _has_column(table: str, column: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    cols = {c["name"] for c in inspector.get_columns(table)}
    return column in cols


def upgrade() -> None:
    conn = op.get_bind()
    now = datetime.utcnow().isoformat()
    base_date = "2026-01-01"

    # Ensure offices table has geo-fencing + timezone columns that may not
    # exist if the table was created by a prior dev iteration
    if not _has_column("offices", "geo_fence_radius_meters"):
        op.add_column("offices", sa.Column("geo_fence_radius_meters", sa.Float(), nullable=True))
    if not _has_column("offices", "timezone"):
        op.add_column("offices", sa.Column("timezone", sa.String(60), nullable=True))

    # Ensure employees table has hire_date
    if not _has_column("employees", "hire_date"):
        op.add_column("employees", sa.Column("hire_date", sa.Date(), nullable=True))

    # Ensure country rows exist
    for code, name, currency in [("OM", "Oman", "OMR"), ("AE", "UAE", "AED"), ("SA", "Saudi Arabia", "SAR")]:
        row = conn.execute(sa.text("SELECT 1 FROM country_configs WHERE code = :c"), {"c": code}).first()
        if not row:
            conn.execute(
                sa.text("INSERT INTO country_configs (code, name, currency) VALUES (:c, :n, :cur)"),
                {"c": code, "n": name, "cur": currency},
            )

    # Create offices and map them
    office_id = {}
    for code, offices in OFFICES.items():
        office_id[code] = []
        for name, city, lat, lng, radius, tz in offices:
            result = conn.execute(
                sa.text(
                    "INSERT INTO offices (country_code, name, city, latitude, longitude, "
                    "geo_fence_radius_meters, timezone, is_active) "
                    "VALUES (:cc, :n, :c, :lat, :lng, :r, :tz, 1)"
                ),
                {"cc": code, "n": name, "c": city, "lat": lat, "lng": lng, "r": radius, "tz": tz},
            )
            office_id[code].append(result.lastrowid)

    # Find admin user
    admin = conn.execute(sa.text("SELECT id FROM users WHERE role = 'admin' LIMIT 1")).first()
    admin_id = admin[0] if admin else None

    # Create employees
    for emp in EMPLOYEES:
        code = emp[1]
        office_idx = emp[7]
        oid = office_id[code][office_idx]
        conn.execute(
            sa.text(
                "INSERT INTO employees (user_id, employee_code, country_code, office_id, "
                "department, position, employment_type, employment_status, salary, currency, "
                "is_verified, hire_date, created_at, updated_at) "
                "VALUES (:uid, :ec, :cc, :oid, :dept, :pos, :etype, 'active', :sal, :cur, 1, :hd, :now, :now)"
            ),
            {
                "uid": admin_id,
                "ec": emp[0],
                "cc": code,
                "oid": oid,
                "dept": emp[2],
                "pos": emp[3],
                "etype": emp[4],
                "sal": emp[5],
                "cur": emp[6],
                "hd": base_date,
                "now": now,
            },
        )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM employees"))
    conn.execute(sa.text("DELETE FROM offices"))

