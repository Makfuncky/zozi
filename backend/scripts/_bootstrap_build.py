import infrastructure.database.database as dbmod
from infrastructure.database.base import Base

# 1) Import every domains/*/models module so all ORM classes/mappers resolve
#    (relationship targets like ShippingCarrier, BankTransaction, ...).
import importlib, pkgutil
def _import_all_models(pkg_name):
    try:
        pkg = importlib.import_module(pkg_name)
    except Exception:
        return
    for _m in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
        try:
            importlib.import_module(_m.name)
        except Exception:
            pass

for _d in ("accounts","catalog","orders","finance","suppliers","logistics",
          "comms","hr","promotions","security","governance","analytics",
          "country","customers","audit"):
    _import_all_models(f"domains.{_d}.models")

# 2) Prune tables whose FKs reference tables not registered in metadata.
#    (resolved by table object so dict-key/schema mismatches don't mask removals)
for _pass in range(10):
    broken = set()
    valid_keys = set(Base.metadata.tables.keys())
    for table in list(Base.metadata.tables.values()):
        for fk in table.foreign_key_constraints:
            try:
                tgt = fk.referred_table
            except Exception:
                broken.add(table)
                break
            if tgt is None or tgt.key not in valid_keys:
                broken.add(table)
                break
    if not broken:
        break
    for t in broken:
        try:
            Base.metadata.remove(t)
        except Exception:
            pass

# 4) Create all tables on the real engine (schema_translate_map strips schemas at DDL time).
Base.metadata.create_all(bind=dbmod.engine)
print("created tables:", len(Base.metadata.tables))

# 5) Gap tables (from Alembic, no/incomplete ORM model) -- copied from conftest.
from sqlalchemy import text
_GAP_DDL = {
    "onboarding_pipelines": """
        CREATE TABLE IF NOT EXISTS onboarding_pipelines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL UNIQUE REFERENCES employees(id) ON DELETE CASCADE,
            country_code TEXT REFERENCES country_configs(code),
            current_step TEXT, total_steps INTEGER DEFAULT 0, completed_steps INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending', started_at TIMESTAMP, due_date TIMESTAMP, completed_at TIMESTAMP,
            notes TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
    "onboarding_steps": """
        CREATE TABLE IF NOT EXISTS onboarding_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pipeline_id INTEGER NOT NULL REFERENCES onboarding_pipelines(id) ON DELETE CASCADE,
            employee_id INTEGER REFERENCES employees(id) ON DELETE CASCADE, step_name TEXT NOT NULL,
            label TEXT, description TEXT, sla_hours INTEGER DEFAULT 24, step_order INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending', completed_at TIMESTAMP, completed_by INTEGER REFERENCES users(id),
            notes TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
    "offboarding_cases": """
        CREATE TABLE IF NOT EXISTS offboarding_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
            country_code TEXT REFERENCES country_configs(code), reason TEXT, status TEXT DEFAULT 'in_progress',
            total_steps INTEGER DEFAULT 6, completed_steps INTEGER DEFAULT 0, current_step TEXT,
            initiated_by INTEGER NOT NULL REFERENCES users(id), initiated_at TIMESTAMP, notice_period_days INTEGER DEFAULT 30,
            proposed_exit_date TIMESTAMP, completed_at TIMESTAMP, cancellation_reason TEXT, cancelled_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
    "employee_activity_logs": """
        CREATE TABLE IF NOT EXISTS employee_activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, actor_employee_id INTEGER REFERENCES employees(id) ON DELETE SET NULL,
            target_employee_id INTEGER REFERENCES employees(id) ON DELETE SET NULL, action TEXT NOT NULL,
            entity_type TEXT, entity_id INTEGER, metadata_json TEXT, country_code TEXT REFERENCES country_configs(code),
            ip_address TEXT, device_fingerprint TEXT, session_id TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
    "employee_bank_accounts": """
        CREATE TABLE IF NOT EXISTS employee_bank_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
            account_holder_name TEXT NOT NULL, bank_name TEXT NOT NULL, account_number_encrypted TEXT NOT NULL,
            iban TEXT, swift_code TEXT, currency TEXT DEFAULT 'OMR', is_primary INTEGER DEFAULT 0, is_verified INTEGER DEFAULT 0,
            verified_at TIMESTAMP, is_active INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
    "payout_batches": """
        CREATE TABLE IF NOT EXISTS payout_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT, batch_number VARCHAR(50) NOT NULL, country_code VARCHAR(10),
            total_amount NUMERIC(16,4) NOT NULL, item_count INTEGER NOT NULL, status VARCHAR(20) DEFAULT 'pending_approval',
            created_by INTEGER REFERENCES users(id), approved_by INTEGER REFERENCES users(id), dispatched_at TIMESTAMP,
            settled_at TIMESTAMP, notes TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
    "journal_entries": """
        CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT, entry_date DATE NOT NULL, description TEXT, reference TEXT,
            total_debit REAL NOT NULL, total_credit REAL NOT NULL, status TEXT DEFAULT 'posted',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
}
with dbmod.engine.connect() as conn:
    for tname, ddl in _GAP_DDL.items():
        conn.execute(text(f"DROP TABLE IF EXISTS {tname}"))
        conn.execute(text("PRAGMA foreign_keys = OFF"))
        conn.execute(text(ddl))
        conn.execute(text("PRAGMA foreign_keys = ON"))
    conn.commit()
print("gap tables created")

# 6) Seed demo accounts + countries (test-suite-proven path) so login works.
#    Ensure related model classes (e.g. ShippingCarrier) are imported so
#    SQLAlchemy can resolve Shipment's relationship before mapper init.
for _m in ("domains.governance.models.admin", "domains.logistics.models.logistics_entities", "domains.logistics.models"):
    try:
        __import__(_m)
    except Exception as _e:
        print("import warn", _m, repr(_e))

from sqlalchemy.orm import sessionmaker
from infrastructure.database.seed import _ensure_demo_user
from domains.accounts.models.user import User as _UserModel
from domains.country.models.countries import CountryConfig

_DEMO_USERS = [
    ("admin@zozi.com", "admin", "admin123", "admin", "admin"),
    ("supplier@zozi.com", "supplier", "supplier123", "supplier", "supplier"),
    ("customer@zozi.com", "customer", "customer123", "customer", "customer"),
]
demo_countries = [
    {"code": "AE", "name": "United Arab Emirates", "currency": "AED", "currency_symbol": "د.إ", "phone_code": "+971"},
    {"code": "SA", "name": "Saudi Arabia", "currency": "SAR", "currency_symbol": "﷼", "phone_code": "+966"},
    {"code": "OM", "name": "Oman", "currency": "OMR", "currency_symbol": "﷼", "phone_code": "+968"},
]

_Session = sessionmaker(bind=dbmod.engine, autoflush=False, autocommit=False)
session = _Session()
try:
    for c in demo_countries:
        if not session.query(CountryConfig).filter(CountryConfig.code == c["code"]).first():
            session.add(CountryConfig(**c))
    session.flush()
    for email, username, password, role, label in _DEMO_USERS:
        _ensure_demo_user(session, email=email, username=username, password=password, role=role, log_label=label)
        if role == "customer":
            u = session.query(_UserModel).filter(_UserModel.email == email).first()
            if u:
                u.email_verified = True
        session.flush()
    session.commit()
    print("demo accounts seeded OK")
except Exception as _e:
    session.rollback()
    print("SEED ERROR:", repr(_e))
finally:
    session.close()

import sqlite3
c = sqlite3.connect("database/zozi.db")
cols = [r[1] for r in c.execute("PRAGMA table_info(users)")]
print("users cols:", cols)
print("email_verified present:", "email_verified" in cols)
n = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
print("users row count:", n)
