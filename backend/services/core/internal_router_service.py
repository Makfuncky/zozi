"""Internal router service - extracted SQLAlchemy DB access from routers.

Service functions accept db: Session as first parameter for FastAPI dependency injection.
"""

import csv
import io
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, func

from data.models import (
    PurchaseOrder, GoodsReceiptNote, SalesOrder, StockMovement,
    Employee, Product, Review,
)


logger = logging.getLogger(__name__)


# =============================================================================
# TRADING ROUTER SERVICE FUNCTIONS
# =============================================================================

def get_purchase_order(db: Session, po_id: int):
    """Fetch a purchase order by ID."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return po


def get_goods_receipt_note(db: Session, grn_id: int):
    """Fetch a goods receipt note by ID."""
    grn = db.query(GoodsReceiptNote).filter(GoodsReceiptNote.id == grn_id).first()
    if not grn:
        raise HTTPException(status_code=404, detail="Goods receipt note not found")
    return grn


def get_sales_order(db: Session, so_id: int):
    """Fetch a sales order by ID."""
    so = db.query(SalesOrder).filter(SalesOrder.id == so_id).first()
    if not so:
        raise HTTPException(status_code=404, detail="Sales order not found")
    return so


def get_stock_movements(
    db: Session,
    product_id: Optional[int] = None,
    warehouse_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
) -> Dict[str, Any]:
    """Get stock levels with movement details."""
    from data.models import Product
    q = db.query(
        StockMovement.product_id,
        Product.name,
        Product.sku,
        func.sum(StockMovement.quantity_change).label("current_stock"),
        func.max(StockMovement.created_at).label("last_movement"),
    ).join(Product, StockMovement.product_id == Product.id)
    if product_id:
        q = q.filter(StockMovement.product_id == product_id)
    if warehouse_id:
        q = q.filter(StockMovement.warehouse_id == warehouse_id)
    q = q.group_by(StockMovement.product_id, Product.name, Product.sku)
    total = q.count()
    rows = q.order_by(StockMovement.id.desc()).offset(offset).limit(limit).all()
    items = []
    for row in rows:
        items.append({
            "product_id": row.product_id,
            "product_name": row.name,
            "sku": row.sku,
            "current_stock": float(row.current_stock or 0),
            "last_movement": row.last_movement.isoformat() if row.last_movement else None,
        })
    return {"total": total, "items": items}


# =============================================================================
# HR DASHBOARD SERVICE FUNCTIONS
# =============================================================================

def get_hr_dashboard_data(
    db: Session,
    country_code: Optional[str] = None,
    days: int = 7,
    skip: int = 0,
    limit: int = 20,
) -> Dict[str, Any]:
    """Return HR dashboard data: onboarding pipeline, performance health, activity feed."""
    result = {}
    country_clause = ""
    params: dict = {"days": days, "skip": skip, "limit": limit}

    if country_code:
        country_clause = " AND country_code = :country_code"
        params["country_code"] = country_code

    now = datetime.utcnow()

    # Onboarding Pipeline Stats
    try:
        pipeline_sql = """
            SELECT
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN status = 'in_progress' AND due_date < :now THEN 1 ELSE 0 END) as overdue,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled
            FROM onboarding_pipelines
            WHERE 1=1 """ + country_clause
        pipeline_counts = db.execute(
            text(pipeline_sql),
            {**params, "now": now},
        ).mappings().first()

        overdue_sql = """
            SELECT p.id, p.employee_id, p.current_step, p.total_steps,
                   p.completed_steps, p.due_date,
                   e.employee_code, e.department, e.position
            FROM onboarding_pipelines p
            LEFT JOIN employees e ON e.id = p.employee_id
            WHERE p.status = 'in_progress' AND p.due_date < :now """ + country_clause + """
            ORDER BY p.due_date ASC
            LIMIT 20
        """
        overdue_items = db.execute(
            text(overdue_sql),
            {**params, "now": now},
        ).mappings().all()

        result["onboarding"] = {
            "stats": dict(pipeline_counts) if pipeline_counts else {"active": 0, "overdue": 0, "completed": 0, "cancelled": 0},
            "overdue_items": [dict(r) for r in overdue_items],
        }
    except Exception as e:
        logger.warning("Onboarding data unavailable (migration may not be run): %s", e)
        result["onboarding"] = {"stats": {"active": 0, "overdue": 0, "completed": 0, "cancelled": 0}, "overdue_items": []}

    # Performance Health Board
    try:
        health_sql = """
            SELECT
                SUM(CASE WHEN performance_score >= 4.0 THEN 1 ELSE 0 END) as green,
                SUM(CASE WHEN performance_score >= 2.5 AND performance_score < 4.0 THEN 1 ELSE 0 END) as amber,
                SUM(CASE WHEN performance_score < 2.5 AND performance_score IS NOT NULL THEN 1 ELSE 0 END) as red,
                SUM(CASE WHEN performance_score IS NULL THEN 1 ELSE 0 END) as not_scored,
                ROUND(AVG(performance_score), 2) as avg_score
            FROM employees
            WHERE employment_status = 'active' """ + country_clause
        health_data = db.execute(
            text(health_sql),
            params,
        ).mappings().first()

        top_sql = """
            SELECT e.id, e.employee_code, e.department, e.position, e.performance_score
            FROM employees e
            WHERE e.employment_status = 'active'
              AND e.performance_score IS NOT NULL """ + country_clause + """
            ORDER BY e.performance_score DESC
            LIMIT 10
        """
        top_performers = db.execute(
            text(top_sql),
            params,
        ).mappings().all()

        bottom_sql = """
            SELECT e.id, e.employee_code, e.department, e.position, e.performance_score
            FROM employees e
            WHERE e.employment_status = 'active'
              AND e.performance_score IS NOT NULL """ + country_clause + """
            ORDER BY e.performance_score ASC
            LIMIT 5
        """
        bottom_performers = db.execute(
            text(bottom_sql),
            params,
        ).mappings().all()

        result["performance"] = {
            "stats": dict(health_data) if health_data else {"green": 0, "amber": 0, "red": 0, "not_scored": 0, "avg_score": None},
            "top_performers": [dict(r) for r in top_performers],
            "bottom_performers": [dict(r) for r in bottom_performers],
        }
    except Exception as e:
        logger.warning("Performance data unavailable (performance_score column may not exist): %s", e)
        result["performance"] = {"stats": {"green": 0, "amber": 0, "red": 0, "not_scored": 0, "avg_score": None}, "top_performers": [], "bottom_performers": []}

    # Recent Activity Feed
    try:
        since_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        params["since"] = since_date

        activity_sql = """
            SELECT al.id, al.actor_employee_id, al.action, al.entity_type,
                   al.entity_id, al.target_employee_id, al.metadata_json,
                   al.created_at,
                   ae.employee_code as actor_code,
                   te.employee_code as target_code
            FROM employee_activity_logs al
            LEFT JOIN employees ae ON ae.id = al.actor_employee_id
            LEFT JOIN employees te ON te.id = al.target_employee_id
            WHERE al.created_at >= :since """ + country_clause + """
            ORDER BY al.created_at DESC
            LIMIT :limit OFFSET :skip
        """
        activity = db.execute(
            text(activity_sql),
            params,
        ).mappings().all()

        total_recent = len(activity)
        action_breakdown: dict = {}
        for a in activity:
            action = a["action"]
            action_breakdown[action] = action_breakdown.get(action, 0) + 1

        result["activity"] = {
            "total_events": total_recent,
            "action_breakdown": action_breakdown,
            "events": [
                {
                    "id": e["id"],
                    "actor_employee_id": e["actor_employee_id"],
                    "actor_code": e["actor_code"],
                    "action": e["action"],
                    "entity_type": e["entity_type"],
                    "target_code": e["target_code"],
                    "timestamp": e["created_at"].isoformat() if e["created_at"] else None,
                }
                for e in activity
            ],
        }
    except Exception as e:
        logger.warning("Activity data unavailable (table may not exist): %s", e)
        result["activity"] = {"total_events": 0, "action_breakdown": {}, "events": []}

    # Employee Counts
    try:
        emp_sql = """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN employment_status = 'active' THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN employment_status = 'terminating' THEN 1 ELSE 0 END) as terminating,
                SUM(CASE WHEN employment_status = 'terminated' THEN 1 ELSE 0 END) as terminated
            FROM employees
            WHERE 1=1 """ + country_clause
        emp_counts = db.execute(
            text(emp_sql),
            params,
        ).mappings().first()
        result["employees"] = dict(emp_counts) if emp_counts else {"total": 0, "active": 0, "terminating": 0, "terminated": 0}
    except Exception as e:
        logger.warning("Employee counts unavailable: %s", e)
        result["employees"] = {"total": 0, "active": 0, "terminating": 0, "terminated": 0}

    result["dashboard_date"] = now.isoformat()
    return result


# =============================================================================
# EXPORTS SERVICE FUNCTIONS
# =============================================================================

def compute_pay_equity_rows(db: Session) -> List[Dict[str, Any]]:
    """Compute pay-equity metrics from employee salary data."""
    rows = (
        db.query(
            Employee.department,
            Employee.gender,
            func.avg(Employee.salary),
        ).filter(Employee.salary.isnot(None), Employee.department.isnot(None))
        .group_by(Employee.department, Employee.gender)
        .all()
    )
    by_dept = {}
    for dept, gender, avg_sal in rows:
        by_dept.setdefault(dept, {})[gender or "unknown"] = float(avg_sal or 0)
    metrics = []
    for dept, vals in by_dept.items():
        avg_male = vals.get("male", 0.0)
        avg_female = vals.get("female", 0.0)
        disparity = (avg_male - avg_female) / avg_male * 100 if (avg_male > 0 and avg_female > 0) else 0.0
        metrics.append({
            "category": dept,
            "avg_male": round(avg_male, 2),
            "avg_female": round(avg_female, 2),
            "disparity_percent": round(disparity, 2),
            "flagged": disparity > 10,
        })
    return metrics


def generate_pay_equity_csv(db: Session) -> tuple:
    """Generate pay-equity CSV data and headers."""
    metrics = compute_pay_equity_rows(db)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["category", "avg_male", "avg_female", "disparity_percent", "flagged"])
    for m in metrics:
        writer.writerow([
            m["category"], m["avg_male"], m["avg_female"],
            m["disparity_percent"], m["flagged"],
        ])
    csv_data = buf.getvalue()
    headers = {
        "Content-Disposition": f"attachment; filename=pay-equity-{datetime.now().date().isoformat()}.csv"
    }
    return csv_data, headers