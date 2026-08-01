"""Employee controller for HCM system with Enterprise Communication & Governance Suite."""
from __future__ import annotations
from datetime import datetime, timezone, date
from typing import Optional, List
from uuid import uuid4
import hashlib
import secrets

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from models.employee_models import (
    Office, Employee, EmployeeDocument, EmployeeAttendance,
    EmployeeWorkLog, EmployeeRelation,
    DynamicQRSession
)
from models import User
from utils.datetime_utils import utcnow as _utcnow
import services.employee_write_service as ew


def list_offices(code: str, db: Session) -> list[dict]:
    offices = db.query(Office).filter(Office.country_code == code).all()
    return [{"id": o.id, "name": o.name, "address": o.address, "city": o.city,
             "latitude": o.latitude,
             "longitude": o.longitude, "is_active": o.is_active} for o in offices]


def create_office(code: str, data: dict, db: Session) -> dict:
    office = ew.create_office(db, code, **data)
    return {"id": office.id, "name": office.name}


def update_office(office_id: int, data: dict, db: Session) -> dict:
    office = db.query(Office).filter(Office.id == office_id).first()
    if not office:
        raise HTTPException(status_code=404, detail="Office not found")
    office = ew.update_office(db, office, data)
    return {"id": office.id, "name": office.name}


def delete_office(office_id: int, db: Session):
    office = db.query(Office).filter(Office.id == office_id).first()
    if not office:
        raise HTTPException(status_code=404, detail="Office not found")
    ew.delete_office(db, office)


def employee_payload(emp: Employee) -> dict:
    return {
        "id": emp.id,
        "employee_code": emp.employee_code,
        "department": emp.department,
        "position": emp.position,
        "employment_status": emp.employment_status,
        "salary": float(emp.salary) if emp.salary else None,
        "currency": emp.currency,
        "country_code": emp.country_code,
        "hire_date": emp.hire_date.isoformat() if emp.hire_date else None,
        "user": {"id": emp.user_id, "full_name": emp.user.full_name if emp.user else None} if emp.user else None,
    }


def list_employees(code: str, db: Session, department: Optional[str] = None,
                   status: Optional[str] = None, query: Optional[str] = None, limit: int = 100) -> list[dict]:
    q = db.query(Employee).filter(Employee.country_code == code)
    if department and department != "all":
        q = q.filter(Employee.department == department)
    if status and status != "all":
        q = q.filter(Employee.employment_status == status)
    if query:
        from models import User
        q = q.join(Employee.user).filter(
            Employee.employee_code.ilike(f"%{query}%") |
            Employee.position.ilike(f"%{query}%") |
            Employee.department.ilike(f"%{query}%") |
            User.full_name.ilike(f"%{query}%") |
            User.username.ilike(f"%{query}%")
        )
    employees = q.order_by(Employee.created_at.desc()).limit(limit).all()
    return [employee_payload(e) for e in employees]


def create_employee(code: str, data: dict, current_user: dict, db: Session) -> dict:
    data["country_code"] = code
    if data.get("hire_date") and isinstance(data["hire_date"], str):
        data["hire_date"] = date.fromisoformat(data["hire_date"])
    emp = ew.create_employee(db, **data)
    return employee_payload(emp)


def get_employee(employee_id: int, db: Session) -> dict:
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee_payload(emp)


def update_employee(employee_id: int, data: dict, current_user: dict, db: Session) -> dict:
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    updates = {}
    for key, value in data.items():
        if key != "password":
            if key == "hire_date" and isinstance(value, str):
                value = date.fromisoformat(value)
            updates[key] = value
    emp = ew.update_employee(db, emp, updates)
    return employee_payload(emp)


def delete_employee(employee_id: int, current_user: dict, db: Session):
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    ew.delete_employee(db, emp)


def list_employee_documents(employee_id: int, db: Session) -> list[dict]:
    docs = db.query(EmployeeDocument).filter(EmployeeDocument.employee_id == employee_id).all()
    return [{"id": d.id, "doc_type": d.doc_type, "file_url": d.file_url, "expiry_date": d.expiry_date} for d in docs]


def create_employee_document(employee_id: int, data: dict, db: Session) -> dict:
    doc = ew.create_employee_document(db, employee_id, **data)
    return {"id": doc.id, "doc_type": doc.doc_type}


def update_employee_document_status(doc_id: int, data: dict, db: Session) -> dict:
    doc = db.query(EmployeeDocument).filter(EmployeeDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc = ew.update_employee_document(db, doc, data)
    return {"id": doc.id, "status": doc.status}


def list_attendance(employee_id: int, db: Session, from_date: Optional[str] = None,
                    to_date: Optional[str] = None, limit: int = 50) -> list[dict]:
    q = db.query(EmployeeAttendance).filter(EmployeeAttendance.employee_id == employee_id)
    if from_date:
        q = q.filter(EmployeeAttendance.date >= datetime.fromisoformat(from_date))
    if to_date:
        q = q.filter(EmployeeAttendance.date <= datetime.fromisoformat(to_date))
    records = q.order_by(EmployeeAttendance.date.desc()).limit(limit).all()
    return [{"id": r.id, "date": r.date.isoformat() if r.date else None,
             "scan_in_time": r.scan_in_time.isoformat() if r.scan_in_time else None,
             "scan_out_time": r.scan_out_time.isoformat() if r.scan_out_time else None,
             "status": r.status} for r in records]


def check_in_employee(employee_id: int, data: dict, db: Session) -> dict:
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    attendance = ew.create_employee_attendance(db, employee_id, **data)
    return {"id": attendance.id, "status": attendance.status}


def check_out_employee(employee_id: int, data: dict, db: Session) -> dict:
    today = datetime.now(timezone.utc).date()
    record = db.query(EmployeeAttendance).filter(
        EmployeeAttendance.employee_id == employee_id,
        EmployeeAttendance.date == today
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="No check-in record found for today")
    record = ew.update_employee_attendance(db, record, data)
    return {"id": record.id, "status": record.status}


def check_in_with_geo(employee_id: int, data: dict, db: Session) -> dict:
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    data.pop("employee_id", None)
    attendance = ew.create_employee_attendance(db, employee_id, **data)
    return {"id": attendance.id, "status": attendance.status}


def validate_geo_location(latitude: float, longitude: float, office_id: int, db: Session) -> dict:
    office = db.query(Office).filter(Office.id == office_id).first()
    if not office:
        raise HTTPException(status_code=404, detail="Office not found")
    if office.latitude and office.longitude:
        from math import radians, sin, cos, sqrt, atan2
        R = 6371000
        lat1, lon1 = radians(office.latitude), radians(office.longitude)
        lat2, lon2 = radians(latitude), radians(longitude)
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance = R * c
        return {"within_fence": distance <= office.geo_fence_radius_meters, "distance_meters": distance}
    return {"within_fence": False, "distance_meters": None}


def list_employee_relations(employee_id: int, db: Session) -> list[dict]:
    relations = db.query(EmployeeRelation).filter(EmployeeRelation.employee_id == employee_id).all()
    return [{"id": r.id, "related_person_name": r.related_person_name,
             "relation_type": r.relation_type, "is_internal": r.is_internal_employee,
             "internal_employee_id": r.internal_employee_id, "notes": None} for r in relations]


def create_employee_relation(employee_id: int, data: dict, db: Session) -> dict:
    relation = ew.create_employee_relation(db, employee_id, **data)
    return {"id": relation.id, "relation_type": relation.relation_type}


def remove_employee_relation(relation_id: int, db: Session):
    relation = db.query(EmployeeRelation).filter(EmployeeRelation.id == relation_id).first()
    if not relation:
        raise HTTPException(status_code=404, detail="Relation not found")
    ew.delete_employee_relation(db, relation)


def list_work_logs(employee_id: int, db: Session, from_date: Optional[str] = None,
                   to_date: Optional[str] = None, status: Optional[str] = None, limit: int = 50) -> list[dict]:
    q = db.query(EmployeeWorkLog).filter(EmployeeWorkLog.employee_id == employee_id)
    if from_date:
        q = q.filter(EmployeeWorkLog.date >= datetime.fromisoformat(from_date))
    if to_date:
        q = q.filter(EmployeeWorkLog.date <= datetime.fromisoformat(to_date))
    if status:
        q = q.filter(EmployeeWorkLog.status == status)
    records = q.order_by(EmployeeWorkLog.date.desc()).limit(limit).all()
    return [{"id": r.id, "date": r.date.isoformat() if r.date else None,
             "hours_worked": float(r.hours_worked), "description": r.task_description} for r in records]


def create_work_log(employee_id: int, data: dict, db: Session) -> dict:
    log = ew.create_employee_work_log(db, employee_id, **data)
    return {"id": log.id, "hours_worked": float(log.hours_worked)}


def approve_work_log(log_id: int, data: dict, current_user: dict, db: Session) -> dict:
    log = db.query(EmployeeWorkLog).filter(EmployeeWorkLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Work log not found")
    log = ew.approve_work_log(db, log, status=data.get("status", "approved"))
    return {"id": log.id, "status": log.status}


def generate_qr_login_token(employee_id: int, db: Session) -> dict:
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    token = str(uuid4())
    session = ew.create_dynamic_qr_session(
        db, employee_id, qr_token=token,
        expires_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    return {"qr_token": token}


def validate_qr_login(token: str, db: Session) -> dict:
    session = db.query(DynamicQRSession).filter(DynamicQRSession.qr_token == token).first()
    if not session or session.expires_at <= datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(status_code=401, detail="Invalid or expired QR token")
    session = ew.update_dynamic_qr_session(
        db, session,
        {"used_at": datetime.now(timezone.utc).replace(tzinfo=None)},
    )
    return {"employee_id": session.employee_id}


def list_employee_roles(code: str, db: Session) -> list[dict]:
    from models.employee_models import EmployeeRole
    roles = db.query(EmployeeRole).all()
    return [{"id": r.id, "name": r.role_name, "permissions": r.permissions} for r in roles]


def create_employee_role(code: str, data: dict, db: Session) -> dict:
    from models.employee_models import EmployeeRole
    if "name" in data:
        data["role_name"] = data.pop("name")
    role = ew.create_employee_role(db, **data)
    return {"id": role.id, "name": role.role_name}


def create_leave_request(employee_id: int, data: dict, current_user: dict, db: Session) -> dict:
    leave = ew.create_leave_request(db, employee_id, **data)
    return {"id": leave.id, "status": leave.status}


def create_shift_roster(employee_id: int, data: dict, current_user: dict, db: Session) -> dict:
    shift = ew.create_shift_roster(db, employee_id, **data)
    return {"id": shift.id, "shift_date": shift.shift_date.isoformat() if shift.shift_date else None}


def kill_switch(employee_id: int, current_user: dict, db: Session) -> dict:
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    user = emp.user
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None)
    if user:
        token = str(uuid4())
        qr_sessions = db.query(DynamicQRSession).filter(DynamicQRSession.employee_id == employee_id)
        ew.apply_kill_switch(
            db,
            jti=token,
            user_id=user.id,
            expires_at=expires_at,
            qr_sessions=qr_sessions,
        )
    else:
        qr_sessions = db.query(DynamicQRSession).filter(DynamicQRSession.employee_id == employee_id)
        ew.update_qr_sessions_expiry(db, qr_sessions, expires_at)
    return {"message": "Kill switch activated", "employee_id": employee_id}


def generate_meeting_token(employee_id: int, db: Session, room_id: Optional[str] = None) -> dict:
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    if emp.user and not emp.user.is_clocked_in:
        raise HTTPException(status_code=403, detail="Employee must be clocked in to start meeting")
    token = secrets.token_urlsafe(32)
    return {"meeting_token": token, "room_id": room_id or f"room_{uuid4().hex[:8]}"}


def create_war_room_chat(db: Session, entity_type: str, entity_id: int, employee_id: int) -> dict:
    chat = {
        "id": uuid4().hex,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "name": f"{entity_type.title()} War Room",
        "created_by": employee_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_active": True
    }
    return chat


def send_entity_chat_message(db: Session, chat_id: str, sender_id: int, content: str, 
                              recipient_type: Optional[str] = None, recipient_id: Optional[int] = None) -> dict:
    msg = {
        "id": uuid4().hex,
        "chat_id": chat_id,
        "sender_id": sender_id,
        "content": content,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "read_by": []
    }
    return msg


def create_masked_communication_channel(db: Session, participant1_id: int, participant2_id: int, 
                                         channel_type: str = "chat") -> dict:
    virtual_number = f"+{secrets.randbelow(9000000000) + 1000000000}"
    channel = {
        "id": uuid4().hex,
        "participant1_id": participant1_id,
        "participant2_id": participant2_id,
        "virtual_number": virtual_number,
        "channel_type": channel_type,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    return channel


def close_communication_channel(db: Session, channel_id: str, reason: str = "completed") -> dict:
    return {"id": channel_id, "status": "closed", "closed_reason": reason}


def generate_email_alias(employee_id: int, country_code: str, db: Session) -> dict:
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    alias = f"{emp.department.lower()}.{country_code.lower()}@zozi.com"
    return {"email_alias": alias, "employee_id": employee_id}


def send_treasury_email(db: Session, template_id: str, recipient_alias: str, 
                         variables: dict, priority: str = "normal") -> dict:
    email_id = uuid4().hex
    return {
        "id": email_id,
        "template_id": template_id,
        "recipient": recipient_alias,
        "variables": variables,
        "priority": priority,
        "status": "sent",
        "sent_at": datetime.now(timezone.utc).isoformat()
    }


def scan_outgoing_dlp(content: str) -> dict:
    pii_patterns = [r'\b\d{10}\b', r'\b\d{15}\b', r'[A-Z]{2}\d{7}\b']
    import re
    for pattern in pii_patterns:
        if re.search(pattern, content):
            return {"blocked": True, "reason": "PII detected", "content_preview": content[:50]}
    return {"blocked": False}


def create_shift_handover_channel(db: Session, shift_date: str, outgoing_shift_id: int) -> dict:
    return {
        "id": uuid4().hex,
        "shift_date": shift_date,
        "outgoing_shift_id": outgoing_shift_id,
        "alerts": [],
        "tickets": [],
        "notes": [],
        "requires_acknowledgment": True
    }


def get_shift_handover_summary(db: Session, channel_id: str) -> dict:
    return {
        "channel_id": channel_id,
        "system_alerts": [],
        "unresolved_tickets": 0,
        "pending_notes": 0,
        "acknowledged": False
    }


def acknowledge_shift_handover(db: Session, channel_id: str, employee_id: int) -> dict:
    return {
        "channel_id": channel_id,
        "acknowledged_by": employee_id,
        "acknowledged_at": datetime.now(timezone.utc).isoformat()
    }


def get_employee_communication_stats(db: Session, employee_id: int) -> dict:
    return {
        "employee_id": employee_id,
        "total_chats": 0,
        "total_meetings": 0,
        "emails_sent": 0,
        "emails_received": 0,
        "last_active": datetime.now(timezone.utc).isoformat()
    }
