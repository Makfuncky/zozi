"""
Seed the operational data the browser journeys need.

The Neon dev database has catalogue and user data but none of the operational
records, so the logistics, employee and admin journeys had nothing to act on:

  hr.employee_attendances     0 rows  -> no clock-in/out, no attendance list
  hr.employee_leave_requests  0 rows  -> no leave request/approval flow
  hr.employee_leave_ledgers   0 rows  -> no leave balance
  logistics.shipments         1 row, and assigned_partner_id is NULL, so the
                               logistics partner's manifest is empty

This inserts enough rows to exercise those flows, and is idempotent: re-running
it will not duplicate anything.

Usage (from backend/):
    python -m scripts._seed_browser_journey_data
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
for line in (BACKEND.parent / ".env").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

import asyncpg  # noqa: E402

EMPLOYEE_EMAIL = "ae.manager@zozi.com"
LOGISTICS_EMAIL = "logistics@zozi.com"
SUPPLIER_EMAIL = "supplier@zozi.com"

TODAY = date.today()


async def main() -> None:
    url = os.environ["DATABASE_URL_DIRECT"].replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(url)
    try:
        emp_user = await conn.fetchrow(
            "SELECT id, country_code FROM accounts.users WHERE email=$1", EMPLOYEE_EMAIL
        )
        logi = await conn.fetchrow(
            "SELECT id, country_code FROM accounts.users WHERE email=$1", LOGISTICS_EMAIL
        )
        supp = await conn.fetchrow(
            "SELECT id, country_code FROM accounts.users WHERE email=$1", SUPPLIER_EMAIL
        )
        order = await conn.fetchrow(
            "SELECT id FROM orders.orders ORDER BY id DESC LIMIT 1"
        )
        # hr.* tables key on hr.employees.id, not accounts.users.id.
        emp = (
            await conn.fetchrow("SELECT id, country_code FROM hr.employees WHERE user_id=$1", emp_user["id"])
            if emp_user
            else None
        )
        if not (emp and logi and supp and order):
            missing = [
                n
                for n, v in (("employee", emp), ("logistics", logi), ("supplier", supp), ("order", order))
                if not v
            ]
            print(f"cannot seed, missing: {', '.join(missing)}")
            return

        cc = emp["country_code"] or "AE"
        print(
            f"employee hr.id={emp['id']} (user {emp_user['id']}) "
            f"logistics user id={logi['id']} supplier id={supp['id']} order={order['id']}"
        )

        # ── Leave ledgers ────────────────────────────────────────────────
        added = 0
        for leave_type, allocated in (("annual", 30), ("sick", 10), ("personal", 5)):
            exists = await conn.fetchval(
                "SELECT 1 FROM hr.employee_leave_ledgers WHERE employee_id=$1 AND leave_type=$2 AND year=$3",
                emp["id"], leave_type, TODAY.year,
            )
            if not exists:
                await conn.execute(
                    """INSERT INTO hr.employee_leave_ledgers
                       (employee_id, leave_type, year, allocated_days, used_days,
                        carried_forward, is_deleted, country_code, created_at, updated_at, version)
                       VALUES ($1,$2,$3,$4,$5,0,false,$6,now(),now(),1)""",
                    emp["id"], leave_type, TODAY.year, allocated, 3 if leave_type == "annual" else 1, cc,
                )
                added += 1
        print(f"leave ledgers inserted: {added}")

        # ── Leave requests (mixed states so approval is exercisable) ─────
        requests = [
            ("annual", TODAY + timedelta(days=12), TODAY + timedelta(days=16), 5, "pending"),
            ("sick", TODAY - timedelta(days=9), TODAY - timedelta(days=8), 2, "approved"),
            ("personal", TODAY + timedelta(days=30), TODAY + timedelta(days=30), 1, "rejected"),
        ]
        added = 0
        for leave_type, start, end, days, status in requests:
            exists = await conn.fetchval(
                """SELECT 1 FROM hr.employee_leave_requests
                   WHERE employee_id=$1 AND start_date=$2 AND leave_type=$3""",
                emp["id"], start, leave_type,
            )
            if not exists:
                await conn.execute(
                    """INSERT INTO hr.employee_leave_requests
                       (employee_id, leave_type, start_date, end_date, days_requested, status,
                        approved_by_id, approved_at, rejection_reason, is_deleted,
                        country_code, created_at, updated_at, version)
                       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,false,$10,now(),now(),1)""",
                    emp["id"], leave_type, start, end, days, status,
                    19 if status in ("approved", "rejected") else None,
                    datetime.utcnow() if status in ("approved", "rejected") else None,
                    "insufficient balance" if status == "rejected" else None,
                    cc,
                )
                added += 1
        print(f"leave requests inserted: {added}")

        # ── Attendance: last 10 weekdays, clocked in/out ─────────────────
        added = 0
        d = TODAY - timedelta(days=1)
        while added < 10:
            if d.weekday() < 5:
                exists = await conn.fetchval(
                    "SELECT 1 FROM hr.employee_attendances WHERE employee_id=$1 AND record_date=$2",
                    emp["id"], d,
                )
                if not exists:
                    # status must satisfy chk_employee_attendance_status_valid:
                    # present | absent | late | half_day | on_leave | holiday
                    status = "late" if added % 4 == 3 else "present"
                    await conn.execute(
                        """INSERT INTO hr.employee_attendances
                           (employee_id, record_date, scan_in_time, scan_out_time, scan_type,
                            location_lat, location_long, device_fingerprint, is_anomaly, status,
                            is_deleted, country_code, created_at, updated_at, version)
                           VALUES ($1,$2,$3,$4,'office',24.2048,55.2708,'e2e-device',false,$5,
                                   false,$6,now(),now(),1)""",
                        emp["id"], d,
                        datetime.combine(d, datetime.min.time()).replace(hour=8, minute=30),
                        datetime.combine(d, datetime.min.time()).replace(hour=17, minute=15),
                        status,
                        cc,
                    )
                    added += 1
            d -= timedelta(days=1)
        print(f"attendance records inserted: {added}")

        # ── Shipments assigned to the logistics partner, one per status ──
        plan = [
            ("E2E-PICKUP", "pickup_ready", 1),
            ("E2E-TRANSIT", "in_transit", 2),
            ("E2E-OUT", "out_for_delivery", 3),
            ("E2E-DELIVERED", "delivered", 4),
        ]
        added = 0
        for tracking, status, packages in plan:
            exists = await conn.fetchval(
                "SELECT 1 FROM logistics.shipments WHERE tracking_number=$1", tracking
            )
            if not exists:
                await conn.execute(
                    """INSERT INTO logistics.shipments
                       (order_id, supplier_id, assigned_partner_id, tracking_number, carrier_name,
                        status_code, package_count, package_weight_kg, current_hub, country_code,
                        version, is_deleted, created_at, updated_at)
                       VALUES ($1,$2,$3,$4,'ZOZI Logistics',$5,$6,2.5,'Dubai Hub',$7,1,false,now(),now())""",
                    order["id"], supp["id"], logi["id"], tracking, status, packages,
                    logi["country_code"] or "AE",
                )
                await conn.execute(
                    """INSERT INTO logistics.shipment_events
                       (shipment_id, event_type, supplier_id, location, notes,
                        country_code, version, is_deleted, created_at, updated_at)
                       SELECT id, 'seeded', $1, 'Dubai Hub', 'seeded for browser journey',
                              $2, 1, false, now(), now()
                       FROM logistics.shipments WHERE tracking_number=$3""",
                    supp["id"], cc, tracking,
                )
                added += 1
        print(f"shipments inserted: {added}")

        # ── Backfill the pre-existing unassigned shipment ────────────────
        fixed = await conn.execute(
            """UPDATE logistics.shipments SET assigned_partner_id=$1
               WHERE tracking_number='TRACK-DEMO-PICKUP-READY-00' AND assigned_partner_id IS NULL""",
            logi["id"],
        )
        print(f"existing shipment reassigned: {fixed}")

        print("\nverification:")
        for label, q in (
            ("employee_attendances", "SELECT count(*) FROM hr.employee_attendances WHERE employee_id=%s" % emp["id"]),
            ("employee_leave_requests", "SELECT count(*) FROM hr.employee_leave_requests WHERE employee_id=%s" % emp["id"]),
            ("employee_leave_ledgers", "SELECT count(*) FROM hr.employee_leave_ledgers WHERE employee_id=%s" % emp["id"]),
            ("shipments for partner", "SELECT count(*) FROM logistics.shipments WHERE assigned_partner_id=%s" % logi["id"]),
        ):
            print(f"   {label:26} {await conn.fetchval(q)}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())