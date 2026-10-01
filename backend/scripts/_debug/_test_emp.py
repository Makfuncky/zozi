import json
import sqlite3
import sys
sys.path.insert(0, '.')
from scripts.seed_loader import _load_json, _filter_by_country

conn = sqlite3.connect('var/zozi.db')
conn.execute("PRAGMA foreign_keys = ON")
cur = conn.cursor()
data = _load_json("employees_full.json").get("employees", [])
rows = _filter_by_country(data, "ALL")
now = "2026-09-04T22:00:00"
sql = "INSERT OR IGNORE INTO employees (id, user_id, employee_code, office_id, department, position, employment_type, employment_status, salary, currency, country_code, hire_date, termination_date, is_verified, gender, years_of_experience, performance_score, education_level, notes, reporting_manager_id, hiring_manager_id, authority_level, org_unit_id, is_deleted, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
for e in rows:
    tup = (e["id"], e["user_id"], e.get("employee_code"), e.get("office_id"), e.get("department"),
           e.get("position"), e.get("employment_type","full_time"), e.get("employment_status","active"),
           e.get("salary"), e.get("currency","AED" if e["country_code"]=="AE" else "SAR"),
           e["country_code"], e.get("hire_date") or "2026-01-01", e.get("termination_date"),
           1 if e.get("is_verified") else 0, e.get("gender"), e.get("years_of_experience"),
           e.get("performance_score"), e.get("education_level"), e.get("notes"),
           e.get("reporting_manager_id"), e.get("hiring_manager_id"), e.get("authority_level",1),
           e.get("org_unit_id"), 0, now, now)
    try:
        cur.execute(sql, tup)
        print(f"  inserted id={e['id']}")
    except Exception as ex:
        print(f"  id={e['id']} {e.get('employee_code')}: {type(ex).__name__}: {ex}")
conn.commit()
