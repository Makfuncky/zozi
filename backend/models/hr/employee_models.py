"""Employee models for HCM system."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Index, Integer, JSON, Numeric, String, Text, UniqueConstraint, BigInteger, Time
from sqlalchemy.orm import relationship
from . import Base
from utils.datetime_utils import utcnow as _utcnow
from ..mixins import TenantMixin

if TYPE_CHECKING:
    from . import User

__all__ = [
    "Office", "PhysicalIDCard", "DynamicQRSession", "EmployeeBiometric",
    "GeoFenceLog", "EmployeeRole", "Employee", "EmployeeAttendance",
    "EmployeeWorkLog", "EmployeeLeaveRequest", "EmployeeLeaveLedger", "EmployeeShiftRoster",
    "EmployeeAddress", "EmployeeDependent", "EmployeeAsset",
    "EmployeeCertification", "EmployeeDocument", "EmployeeRelation",
    "COIReport", "TravelRequest", "AlumniNetwork", "DisciplinaryCase", "OffboardingCase",
    "OrgUnit", "TrainingModule", "EmployeeTraining",
    "ActivityLog", "ApprovalRequest",
]

class Office(Base, TenantMixin):
    __tablename__ = "offices"
    __table_args__ = ({"schema": "hr"},)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    geo_fence_radius_meters = Column(Integer, default=100)
    address = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(200), nullable=True)

class PhysicalIDCard(Base, TenantMixin):
    __tablename__ = "physical_id_cards"
    __table_args__ = ({"schema": "hr"},)
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id"), unique=True, nullable=False)
    card_number = Column(String(50), unique=True, nullable=False, index=True)
    issued_at = Column(DateTime, default=_utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    employee = relationship("Employee")

class DynamicQRSession(Base, TenantMixin):
    __tablename__ = "dynamic_qr_sessions"
    __table_args__ = (Index("ix_qr_session_employee_expires", "employee_id", "expires_at"), {"schema": "hr"})
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id"), nullable=False)
    qr_token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    device_fingerprint = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    employee = relationship("Employee", back_populates="dynamic_qr_sessions")

class EmployeeBiometric(Base, TenantMixin):
    __tablename__ = "employee_biometrics"
    __table_args__ = ({"schema": "hr"},)
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id"), unique=True, nullable=False)
    fingerprint_hash = Column(String(255), nullable=True)
    face_encoding = Column(Text, nullable=True)
    biometric_type = Column(String(20), default="fingerprint")
    enrolled_at = Column(DateTime, default=_utcnow)

    employee = relationship("Employee", back_populates="biometrics", uselist=False)

class GeoFenceLog(Base, TenantMixin):
    __tablename__ = "geo_fence_logs"
    __table_args__ = ({"schema": "hr"},)
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id"), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    accuracy_meters = Column(Integer, nullable=True)
    scanned_at = Column(DateTime, default=_utcnow)
    is_within_fence = Column(Boolean, default=False)

    employee = relationship("Employee", back_populates="geo_fence_logs")

class EmployeeRole(Base, TenantMixin):
    __tablename__ = "employee_roles"
    __table_args__ = ({"schema": "hr"},)
    id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(100), unique=True)
    permissions = Column(JSON)
    authority_level = Column(Integer, nullable=True)
    can_approve_leave = Column(Boolean, default=False)
    can_approve_expense = Column(Boolean, default=False)
    can_manage_users = Column(Boolean, default=False)

class OrgUnit(Base, TenantMixin):
    __tablename__ = "org_units"
    __table_args__ = ({"schema": "hr"},)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    parent_id = Column(Integer, ForeignKey("hr.org_units.id"), nullable=True)

    parent = relationship("OrgUnit", remote_side=[id], backref="children")

class Employee(Base, TenantMixin):
    __tablename__ = "employees"
    __table_args__ = (
        UniqueConstraint("employee_code", name="uq_employees_code"),
        Index("ix_employees_user_id", "user_id"),
        Index("ix_employees_office", "office_id"), {"schema": "hr"})
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id", ondelete="CASCADE"), unique=True)
    employee_code = Column(String(20), unique=True, nullable=False)
    office_id = Column(Integer, ForeignKey("hr.offices.id", ondelete="SET NULL"), nullable=True)
    department = Column(String(100), nullable=True)
    position = Column(String(100), nullable=True)
    employment_type = Column(String(30), default="full_time")
    employment_status = Column(String(30), default="active")
    salary = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(3), default="OMR")

    termination_date = Column(Date, nullable=True)
    is_verified = Column(Boolean, default=False)
    gender = Column(String(20), nullable=True)
    years_of_experience = Column(Integer, nullable=True)
    performance_score = Column(Integer, nullable=True)
    education_level = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    reporting_manager_id = Column(Integer, ForeignKey("hr.employees.id"), nullable=True)
    hiring_manager_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    authority_level = Column(Integer, nullable=True)
    org_unit_id = Column(Integer, ForeignKey("hr.org_units.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(3), ForeignKey("country.country_configs.code"), nullable=True)

    user = relationship("User", foreign_keys=[user_id], backref="employee_profile")
    office = relationship("Office", backref="employees")
    country = relationship("CountryConfig", foreign_keys="Employee.country_code")
    reports_to = relationship("Employee", remote_side=[id], backref="subordinates")
    hiring_manager = relationship("User", foreign_keys=[hiring_manager_id])
    org_unit = relationship("OrgUnit", backref="employees")
    addresses = relationship("EmployeeAddress", back_populates="employee", cascade="all, delete-orphan")
    dependents = relationship("EmployeeDependent", back_populates="employee", cascade="all, delete-orphan")
    assets = relationship("EmployeeAsset", back_populates="employee", cascade="all, delete-orphan")
    certifications = relationship("EmployeeCertification", back_populates="employee", cascade="all, delete-orphan")
    documents = relationship("EmployeeDocument", back_populates="employee", cascade="all, delete-orphan")
    relations = relationship("EmployeeRelation", back_populates="employee", cascade="all, delete-orphan", foreign_keys="EmployeeRelation.employee_id")
    work_logs = relationship("EmployeeWorkLog", back_populates="employee", cascade="all, delete-orphan")
    trainings = relationship("EmployeeTraining", back_populates="employee", cascade="all, delete-orphan")
    attendance = relationship("EmployeeAttendance", back_populates="employee", cascade="all, delete-orphan")
    leave_requests = relationship("EmployeeLeaveRequest", back_populates="employee", cascade="all, delete-orphan")
    leave_ledgers = relationship("EmployeeLeaveLedger", back_populates="employee", cascade="all, delete-orphan")
    shift_rosters = relationship("EmployeeShiftRoster", back_populates="employee", cascade="all, delete-orphan")
    id_card = relationship("PhysicalIDCard", back_populates="employee", uselist=False, cascade="all, delete-orphan")
    dynamic_qr_sessions = relationship("DynamicQRSession", back_populates="employee", cascade="all, delete-orphan")
    biometrics = relationship("EmployeeBiometric", back_populates="employee", uselist=False, cascade="all, delete-orphan")
    geo_fence_logs = relationship("GeoFenceLog", back_populates="employee", cascade="all, delete-orphan")

class EmployeeAttendance(Base, TenantMixin):
    __tablename__ = "employee_attendance"
    __table_args__ = (
        UniqueConstraint("employee_id", "date", name="uq_attendance_employee_date"),
        Index("ix_attendance_employee", "employee_id"),
        Index("ix_attendance_date", "date"),
        {"schema": "hr"})

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    scan_in_time = Column(DateTime, nullable=True)
    scan_out_time = Column(DateTime, nullable=True)
    scan_type = Column(String(20), nullable=True)
    location_lat = Column(Float, nullable=True)
    location_long = Column(Float, nullable=True)
    device_fingerprint = Column(String(255), nullable=True)
    is_anomaly = Column(Boolean, default=False)
    status = Column(String(20), default="present")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    employee = relationship("Employee", back_populates="attendance")

class EmployeeWorkLog(Base, TenantMixin):
    __tablename__ = "employee_work_logs"
    __table_args__ = ({"schema": "hr"},)
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    hours_worked = Column(Numeric(5, 2), default=0)
    task_description = Column(Text, nullable=True)
    location_lat = Column(Float, nullable=True)
    location_long = Column(Float, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    employee = relationship("Employee", back_populates="work_logs")

class EmployeeLeaveRequest(Base, TenantMixin):
    __tablename__ = "employee_leave_requests"
    __table_args__ = ({"schema": "hr"},)
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="CASCADE"), nullable=False, index=True)
    leave_type = Column(String(50), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days_requested = Column(Integer, nullable=False)
    status = Column(String(20), default="pending")
    approved_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    employee = relationship("Employee", back_populates="leave_requests")
    approver = relationship("User", foreign_keys=[approved_by])

class EmployeeLeaveLedger(Base, TenantMixin):
    __tablename__ = "employee_leave_ledgers"
    __table_args__ = (
        UniqueConstraint("employee_id", "leave_type", "year", name="uq_leave_ledger_employee_type_year"), {"schema": "hr"})
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="CASCADE"), nullable=False, index=True)
    leave_type = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    allocated_days = Column(Integer, default=0)
    used_days = Column(Integer, default=0)
    carried_forward = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    employee = relationship("Employee", back_populates="leave_ledgers")

class EmployeeShiftRoster(Base, TenantMixin):
    __tablename__ = "employee_shift_rosters"
    __table_args__ = (UniqueConstraint("employee_id", "shift_date", name="uq_shift_employee_date"), {"schema": "hr"})
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="CASCADE"), nullable=False, index=True)
    shift_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    shift_type = Column(String(30), default="scheduled")
    status = Column(String(20), default="scheduled")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    employee = relationship("Employee", back_populates="shift_rosters")

class EmployeeAsset(Base, TenantMixin):
    __tablename__ = "employee_assets"
    __table_args__ = ({"schema": "hr"},)
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_type = Column(String(50), nullable=False)
    asset_id = Column(String(100), nullable=False)
    serial_no = Column(String(100), nullable=True)
    assigned_at = Column(DateTime, default=_utcnow)
    returned_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="assigned")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    employee = relationship("Employee", back_populates="assets")

class EmployeeCertification(Base, TenantMixin):
    __tablename__ = "employee_certifications"
    __table_args__ = ({"schema": "hr"},)
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="CASCADE"), nullable=False, index=True)
    cert_type = Column(String(100), nullable=False)
    cert_name = Column(String(200), nullable=False)
    issued_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    is_valid = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    employee = relationship("Employee", back_populates="certifications")

class EmployeeDocument(Base, TenantMixin):
    __tablename__ = "employee_documents"
    __table_args__ = ({"schema": "hr"},)
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="CASCADE"), nullable=False, index=True)
    doc_type = Column(String(50), nullable=False)
    file_url = Column(String(500), nullable=False)
    expiry_date = Column(Date, nullable=True)
    verified_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    employee = relationship("Employee", back_populates="documents")
    verifier = relationship("User", foreign_keys=[verified_by])

class EmployeeDependent(Base, TenantMixin):
    __tablename__ = "employee_dependents"
    __table_args__ = ({"schema": "hr"},)
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(160), nullable=False)
    relation = Column(String(50), nullable=False)
    dob = Column(Date, nullable=True)
    is_insured = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    employee = relationship("Employee", back_populates="dependents")

class EmployeeRelation(Base, TenantMixin):
    __tablename__ = "employee_relations"
    __table_args__ = ({"schema": "hr"},)
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="CASCADE"), nullable=False, index=True)
    related_person_name = Column(String(160), nullable=False)
    relation_type = Column(String(30), nullable=False)
    is_internal_employee = Column(Boolean, default=False)
    internal_employee_id = Column(Integer, ForeignKey("hr.employees.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    employee = relationship("Employee", back_populates="relations", foreign_keys=[employee_id])
    internal_employee = relationship("Employee", foreign_keys=[internal_employee_id])

class EmployeeAddress(Base, TenantMixin):
    __tablename__ = "employee_addresses"
    __table_args__ = ({"schema": "hr"},)
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="CASCADE"), nullable=False, index=True)
    address_type = Column(String(30), nullable=False)
    street = Column(String(200), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)

    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(3), ForeignKey("country.country_configs.code"), nullable=True)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    employee = relationship("Employee", back_populates="addresses")
    country = relationship("CountryConfig", foreign_keys="EmployeeAddress.country_code")

class COIReport(Base, TenantMixin):
    __tablename__ = "coi_reports"
    __table_args__ = ({"schema": "hr"},)
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id"), nullable=False)
    related_person_name = Column(String(160), nullable=False)
    relation_type = Column(String(30), nullable=False)
    is_internal = Column(Boolean, default=False)
    internal_employee_id = Column(Integer, ForeignKey("hr.employees.id"), nullable=True)
    risk_level = Column(String(20), default="low")
    is_approved = Column(Boolean, default=False)
    approved_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    internal_employee = relationship("Employee", foreign_keys=[internal_employee_id])
    approver = relationship("User", foreign_keys=[approved_by])

class TravelRequest(Base, TenantMixin):
    __tablename__ = "employee_travel_requests"
    __table_args__ = ({"schema": "hr"},)
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id"), nullable=False)
    destination_country = Column(String(10), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    purpose = Column(String(200), nullable=True)
    status = Column(String(20), default="pending")
    approved_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    per_diem_json = Column(JSON, nullable=True)
    total_cost = Column(Numeric(12, 2), nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    employee = relationship("Employee", backref="travel_requests")
    approver = relationship("User", foreign_keys=[approved_by])

class AlumniNetwork(Base, TenantMixin):
    __tablename__ = "alumni_network"
    __table_args__ = ({"schema": "hr"},)
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id"), unique=True, nullable=False)
    status = Column(String(20), default="active")
    granted_at = Column(DateTime, default=_utcnow)
    eligibility_expires_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    employee = relationship("Employee", backref="alumni_record")

class DisciplinaryCase(Base, TenantMixin):
    __tablename__ = "disciplinary_cases"
    __table_args__ = ({"schema": "hr"},)
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id"), nullable=False, index=True)
    employee_name = Column(String(200), nullable=True)
    stage = Column(String(30), nullable=False, default="verbal_warning")
    description = Column(Text, nullable=False)
    issued_at = Column(DateTime, default=_utcnow)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=_utcnow)

    employee = relationship("Employee", foreign_keys=[employee_id])

class OffboardingCase(Base, TenantMixin):
    __tablename__ = "offboarding_cases"
    __table_args__ = ({"schema": "hr"},)
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id"), nullable=False, index=True)
    employee_name = Column(String(200), nullable=True)
    reason = Column(String(50), nullable=False, default="resignation")
    status = Column(String(20), default="pending")
    initiated_at = Column(DateTime, default=_utcnow)
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    employee = relationship("Employee", foreign_keys=[employee_id])


class TrainingModule(Base):
    __tablename__ = "training_modules"
    module_id = Column(String(100), primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    required_for_role = Column(String(100), nullable=True)
    duration_minutes = Column(Integer, default=30)
    is_active = Column(Boolean, default=True)
    permission_key = Column(String(100), nullable=True)
    permission_description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    trainings = relationship("EmployeeTraining", back_populates="module", cascade="all, delete-orphan")


class EmployeeTraining(Base, TenantMixin):
    __tablename__ = "employee_trainings"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="CASCADE"), nullable=False, index=True)
    module_id = Column(String(100), ForeignKey("training_modules.module_id"), nullable=False)
    assigned_at = Column(DateTime, nullable=True, server_default="CURRENT_TIMESTAMP")
    completed_at = Column(DateTime, nullable=True)
    score = Column(Numeric(5, 2), nullable=True)
    status = Column(String(20), default="assigned")

    employee = relationship("Employee", back_populates="trainings")
    module = relationship("TrainingModule", back_populates="trainings")


class ActivityLog(Base, TenantMixin):
    """User activity log entry (ESS dashboard feed)."""
    __tablename__ = "activity_logs"
    __table_args__ = ({"schema": "hr"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False, index=True)
    action = Column(String(120), nullable=True)
    entity_type = Column(String(60), nullable=True)
    entity_id = Column(Integer, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class ApprovalRequest(Base, TenantMixin):
    """Approval request assigned to a user (ESS pending approvals)."""
    __tablename__ = "approval_requests"
    __table_args__ = ({"schema": "hr"},)
    id = Column(Integer, primary_key=True, index=True)
    assignee_id = Column(Integer, ForeignKey("core.users.id"), nullable=False, index=True)
    requester_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    approval_type = Column(String(60), nullable=True)
    status = Column(String(20), default="pending", index=True)
    reason = Column(Text, nullable=True)
    decision_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)