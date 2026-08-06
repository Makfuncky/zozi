"""Employee models for HCM system."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Index, Integer, JSON, Numeric, String, Text, UniqueConstraint, BigInteger, Time
from sqlalchemy.orm import relationship
from . import Base
from utils.datetime_utils import utcnow as _utcnow

if TYPE_CHECKING:
    from . import User

__all__ = [
    "Office", "PhysicalIDCard", "DynamicQRSession", "EmployeeBiometric",
    "GeoFenceLog", "EmployeeRole", "Employee", "EmployeeAttendance",
    "EmployeeWorkLog", "EmployeeLeaveRequest", "EmployeeLeaveLedger", "EmployeeShiftRoster",
    "EmployeeAddress", "EmployeeDependent", "EmployeeAsset",
    "EmployeeCertification", "EmployeeDocument", "EmployeeRelation",
    "COIReport", "TravelRequest", "AlumniNetwork", "DisciplinaryCase", "OffboardingCase",
    "OrgUnit",
    "EmployeeBankAccount", "OKRObjective", "KPIMetric", "PerformanceReview",
    "EmailFolder", "InternalEmail", "ChatAttachment", "ChatReadReceipt",
    "EmployeeActivityLog",
]


class Office(Base):
    __tablename__ = "offices"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    country_code = Column(String(10), nullable=False)
    city = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    geo_fence_radius_meters = Column(Integer, default=100)
    address = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)


class PhysicalIDCard(Base):
    __tablename__ = "physical_id_cards"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), unique=True, nullable=False)
    card_number = Column(String(50), unique=True, nullable=False, index=True)
    issued_at = Column(DateTime, default=_utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    
    employee = relationship("Employee")


class DynamicQRSession(Base):
    __tablename__ = "dynamic_qr_sessions"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    qr_token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    device_fingerprint = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    
    employee = relationship("Employee")
    __table_args__ = (Index("ix_qr_session_employee_expires", "employee_id", "expires_at"),)


class EmployeeBiometric(Base):
    __tablename__ = "employee_biometrics"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), unique=True, nullable=False)
    fingerprint_hash = Column(String(255), nullable=True)
    face_encoding = Column(Text, nullable=True)
    biometric_type = Column(String(20), default="fingerprint")
    enrolled_at = Column(DateTime, default=_utcnow)
    is_active = Column(Boolean, default=True)
    country_code = Column(String(10), nullable=True, index=True)
    
    employee = relationship("Employee")


class GeoFenceLog(Base):
    __tablename__ = "geo_fence_logs"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    accuracy_meters = Column(Integer, nullable=True)
    scanned_at = Column(DateTime, default=_utcnow)
    is_within_fence = Column(Boolean, default=False)
    country_code = Column(String(10), nullable=True, index=True)
    
    employee = relationship("Employee")


class EmployeeRole(Base):
    __tablename__ = "employee_roles"
    id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(100), unique=True)
    permissions = Column(JSON)
    authority_level = Column(Integer, nullable=True)
    can_approve_leave = Column(Boolean, default=False)
    can_approve_expense = Column(Boolean, default=False)
    can_manage_users = Column(Boolean, default=False)
    country_code = Column(String(10), nullable=True, index=True)


class OrgUnit(Base):
    __tablename__ = "org_units"
    __table_args__ = (
        Index("ix_org_unit_path", "path"),
        Index("ix_org_unit_parent", "parent_id"),
    )
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    parent_id = Column(Integer, ForeignKey("org_units.id"), nullable=True)
    path = Column(String(500), nullable=True, comment="Materialized path like '/1/12/45/'")
    depth = Column(Integer, default=0, comment="Depth in hierarchy (0 = root)")
    country_code = Column(String(10), nullable=True)
    level = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)

    parent = relationship("OrgUnit", remote_side=[id], backref="children")


class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = (
        UniqueConstraint("employee_code", name="uq_employees_code"),
        Index("ix_employees_user_id", "user_id"),
        Index("ix_employees_office", "office_id"),
    )
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    employee_code = Column(String(20), unique=True, nullable=False)
    office_id = Column(Integer, ForeignKey("offices.id", ondelete="SET NULL"), nullable=True)
    department = Column(String(100), nullable=True)
    position = Column(String(100), nullable=True)
    employment_type = Column(String(30), default="full_time")
    employment_status = Column(String(30), default="active")
    salary = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(3), default="OMR")
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=True)
    hire_date = Column(Date, nullable=False)
    termination_date = Column(Date, nullable=True)
    is_verified = Column(Boolean, default=False)
    gender = Column(String(20), nullable=True)
    years_of_experience = Column(Integer, nullable=True)
    performance_score = Column(Integer, nullable=True)
    education_level = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    reporting_manager_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    hiring_manager_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    authority_level = Column(Integer, nullable=True)
    org_unit_id = Column(Integer, ForeignKey("org_units.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    
    user = relationship("User", foreign_keys=[user_id], backref="employee_profile")
    office = relationship("Office", backref="employees")
    country = relationship("CountryConfig", foreign_keys=[country_code])
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
    attendance = relationship("EmployeeAttendance", back_populates="employee", cascade="all, delete-orphan")
    leave_requests = relationship("EmployeeLeaveRequest", back_populates="employee", cascade="all, delete-orphan")
    leave_ledgers = relationship("EmployeeLeaveLedger", back_populates="employee", cascade="all, delete-orphan")
    shift_rosters = relationship("EmployeeShiftRoster", back_populates="employee", cascade="all, delete-orphan")
    id_card = relationship("PhysicalIDCard", back_populates="employee", uselist=False, cascade="all, delete-orphan")
    dynamic_qr_sessions = relationship("DynamicQRSession", back_populates="employee", cascade="all, delete-orphan")
    biometrics = relationship("EmployeeBiometric", back_populates="employee", uselist=False, cascade="all, delete-orphan")
    geo_fence_logs = relationship("GeoFenceLog", back_populates="employee", cascade="all, delete-orphan")
    bank_accounts = relationship("EmployeeBankAccount", back_populates="employee", cascade="all, delete-orphan")
    objectives = relationship("OKRObjective", back_populates="employee", cascade="all, delete-orphan")
    kpi_metrics = relationship("KPIMetric", back_populates="employee", cascade="all, delete-orphan")
    performance_reviews = relationship("PerformanceReview", back_populates="employee", cascade="all, delete-orphan")
    email_folders = relationship("EmailFolder", back_populates="employee", cascade="all, delete-orphan")
    activity_logs = relationship("EmployeeActivityLog", back_populates="actor", cascade="all, delete-orphan", foreign_keys="EmployeeActivityLog.actor_employee_id")
    activity_logs_targeted = relationship("EmployeeActivityLog", back_populates="target", cascade="all, delete-orphan", foreign_keys="EmployeeActivityLog.target_employee_id")
    active_tasks = relationship("EmployeeActiveTask", back_populates="employee", cascade="all, delete-orphan")
    audit_timeline = relationship("EmployeeAuditTimeline", back_populates="employee", cascade="all, delete-orphan")
    risk_scores = relationship("EmployeeRiskScore", back_populates="employee", cascade="all, delete-orphan")


class EmployeeAttendance(Base):
    __tablename__ = "employee_attendance"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
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
    country_code = Column(String(10), nullable=True, index=True)
    
    employee = relationship("Employee", back_populates="attendance")
    
    __table_args__ = (UniqueConstraint("employee_id", "date", name="uq_attendance_employee_date"),)


class EmployeeWorkLog(Base):
    __tablename__ = "employee_work_logs"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    hours_worked = Column(Numeric(5, 2), default=0)
    task_description = Column(Text, nullable=True)
    location_lat = Column(Float, nullable=True)
    location_long = Column(Float, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    
    employee = relationship("Employee", back_populates="work_logs")


class EmployeeLeaveRequest(Base):
    __tablename__ = "employee_leave_requests"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    leave_type = Column(String(50), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days_requested = Column(Integer, nullable=False)
    status = Column(String(20), default="pending")
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    
    employee = relationship("Employee", back_populates="leave_requests")
    approver = relationship("User", foreign_keys=[approved_by])


class EmployeeLeaveLedger(Base):
    __tablename__ = "employee_leave_ledgers"
    __table_args__ = (
        UniqueConstraint("employee_id", "leave_type", "year", name="uq_leave_ledger_employee_type_year"),
    )
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    leave_type = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    allocated_days = Column(Integer, default=0)
    used_days = Column(Integer, default=0)
    carried_forward = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    
    employee = relationship("Employee", back_populates="leave_ledgers")


class EmployeeShiftRoster(Base):
    __tablename__ = "employee_shift_rosters"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    shift_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    shift_type = Column(String(30), default="scheduled")
    status = Column(String(20), default="scheduled")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    
    employee = relationship("Employee", back_populates="shift_rosters")
    
    __table_args__ = (UniqueConstraint("employee_id", "shift_date", name="uq_shift_employee_date"),)


class EmployeeAsset(Base):
    __tablename__ = "employee_assets"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_type = Column(String(50), nullable=False)
    asset_id = Column(String(100), nullable=False)
    serial_no = Column(String(100), nullable=True)
    assigned_at = Column(DateTime, default=_utcnow)
    returned_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="assigned")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    
    employee = relationship("Employee", back_populates="assets")


class EmployeeCertification(Base):
    __tablename__ = "employee_certifications"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    cert_type = Column(String(100), nullable=False)
    cert_name = Column(String(200), nullable=False)
    issued_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    is_valid = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    
    employee = relationship("Employee", back_populates="certifications")


class EmployeeDocument(Base):
    __tablename__ = "employee_documents"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    doc_type = Column(String(50), nullable=False)
    file_url = Column(String(500), nullable=False)
    expiry_date = Column(Date, nullable=True)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    
    employee = relationship("Employee", back_populates="documents")
    verifier = relationship("User", foreign_keys=[verified_by])


class EmployeeDependent(Base):
    __tablename__ = "employee_dependents"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(160), nullable=False)
    relation = Column(String(50), nullable=False)
    dob = Column(Date, nullable=True)
    is_insured = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    
    employee = relationship("Employee", back_populates="dependents")


class EmployeeRelation(Base):
    __tablename__ = "employee_relations"
    __table_args__ = (
        Index("ix_emp_rel_type", "relation_type"),
        Index("ix_emp_rel_internal", "internal_employee_id"),
    )
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    related_person_name = Column(String(160), nullable=False)
    relation_type = Column(String(30), nullable=False)
    is_internal_employee = Column(Boolean, default=False)
    internal_employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    
    employee = relationship("Employee", back_populates="relations", foreign_keys=[employee_id])
    internal_employee = relationship("Employee", foreign_keys=[internal_employee_id])


class EmployeeAddress(Base):
    __tablename__ = "employee_addresses"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    address_type = Column(String(30), nullable=False)
    street = Column(String(200), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=False)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    
    employee = relationship("Employee", back_populates="addresses")
    country = relationship("CountryConfig", foreign_keys=[country_code])


class COIReport(Base):
    __tablename__ = "coi_reports"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    related_person_name = Column(String(160), nullable=False)
    relation_type = Column(String(30), nullable=False)
    is_internal = Column(Boolean, default=False)
    internal_employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    risk_level = Column(String(20), default="low")
    is_approved = Column(Boolean, default=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    employee = relationship("Employee", foreign_keys=[employee_id])
    internal_employee = relationship("Employee", foreign_keys=[internal_employee_id])
    approver = relationship("User", foreign_keys=[approved_by])


class TravelRequest(Base):
    __tablename__ = "employee_travel_requests"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    destination_country = Column(String(10), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    purpose = Column(String(200), nullable=True)
    status = Column(String(20), default="pending")
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    per_diem_json = Column(JSON, nullable=True)
    total_cost = Column(Numeric(12, 2), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    
    employee = relationship("Employee", backref="travel_requests")
    approver = relationship("User", foreign_keys=[approved_by])


class AlumniNetwork(Base):
    __tablename__ = "alumni_network"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), unique=True, nullable=False)
    status = Column(String(20), default="active")
    granted_at = Column(DateTime, default=_utcnow)
    eligibility_expires_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    
    employee = relationship("Employee", backref="alumni_record")

class DisciplinaryCase(Base):
    __tablename__ = "disciplinary_cases"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    employee_name = Column(String(200), nullable=True)
    stage = Column(String(30), nullable=False, default="verbal_warning")
    description = Column(Text, nullable=False)
    issued_at = Column(DateTime, default=_utcnow)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    
    employee = relationship("Employee", foreign_keys=[employee_id])

class OffboardingCase(Base):
    __tablename__ = "offboarding_cases"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    employee_name = Column(String(200), nullable=True)
    reason = Column(String(50), nullable=False, default="resignation")
    status = Column(String(20), default="pending")
    initiated_at = Column(DateTime, default=_utcnow)
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    
    employee = relationship("Employee", foreign_keys=[employee_id])


class EmployeeBankAccount(Base):
    __tablename__ = "employee_bank_accounts"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    account_holder_name = Column(String(200), nullable=False)
    bank_name = Column(String(200), nullable=False)
    branch_code = Column(String(50), nullable=True)
    account_number_encrypted = Column(String(500), nullable=False)
    iban = Column(String(34), nullable=True)
    swift_code = Column(String(11), nullable=True)
    currency = Column(String(3), default="OMR")
    is_primary = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    change_requested_at = Column(DateTime, nullable=True)
    change_effective_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    
    employee = relationship("Employee", back_populates="bank_accounts")
    verifier = relationship("User", foreign_keys=[verified_by])
    
    __table_args__ = (Index("ix_emp_bank_employee_primary", "employee_id", "is_primary"),)


class OKRObjective(Base):
    __tablename__ = "okr_objectives"
    id = Column(Integer, primary_key=True, index=True)
    parent_objective_id = Column(Integer, ForeignKey("okr_objectives.id"), nullable=True)
    org_unit_id = Column(Integer, nullable=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    objective_type = Column(String(20), default="individual")
    quarter = Column(String(10), nullable=False)
    year = Column(Integer, nullable=False)
    status = Column(String(20), default="draft")
    progress_pct = Column(Integer, default=0)
    confidence_level = Column(Integer, nullable=True)
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    
    parent = relationship("OKRObjective", remote_side=[id], backref="child_objectives")
    employee = relationship("Employee", back_populates="objectives")
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        Index("ix_okr_org_unit", "org_unit_id"),
        Index("ix_okr_employee", "employee_id"),
        Index("ix_okr_quarter", "quarter", "year"),
    )


class KPIMetric(Base):
    __tablename__ = "kpi_metrics"
    id = Column(Integer, primary_key=True, index=True)
    objective_id = Column(Integer, ForeignKey("okr_objectives.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    metric_name = Column(String(200), nullable=False)
    metric_type = Column(String(30), default="number")
    target_value = Column(Numeric(12, 2), nullable=False)
    current_value = Column(Numeric(12, 2), default=0)
    weight_pct = Column(Integer, default=100)
    data_source = Column(String(100), nullable=True)
    auto_source_query = Column(Text, nullable=True)
    last_auto_refreshed_at = Column(DateTime, nullable=True)
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    
    objective = relationship("OKRObjective", backref="kpi_metrics")
    employee = relationship("Employee", back_populates="kpi_metrics")

    __table_args__ = (Index("ix_kpi_objective", "objective_id", "employee_id"),)


class PerformanceReview(Base):
    __tablename__ = "performance_reviews"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    review_cycle = Column(String(30), nullable=False)
    review_type = Column(String(30), default="self")
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    overall_score = Column(Numeric(5, 2), nullable=True)
    rating = Column(String(20), nullable=True)
    comments = Column(Text, nullable=True)
    strengths = Column(Text, nullable=True)
    areas_for_improvement = Column(Text, nullable=True)
    goals_next_period = Column(Text, nullable=True)
    status = Column(String(20), default="pending")
    submitted_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    
    employee = relationship("Employee", back_populates="performance_reviews")
    reviewer = relationship("User", foreign_keys=[reviewer_id])

    __table_args__ = (
        Index("ix_perf_review_cycle", "employee_id", "review_cycle"),
        Index("ix_perf_review_reviewer", "reviewer_id"),
    )


class EmailFolder(Base):
    __tablename__ = "email_folders"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    folder_type = Column(String(20), default="custom")
    icon = Column(String(50), nullable=True)
    sort_order = Column(Integer, default=0)
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    
    employee = relationship("Employee", back_populates="email_folders")

    __table_args__ = (UniqueConstraint("employee_id", "name", name="uq_email_folder_employee_name"),)


class InternalEmail(Base):
    __tablename__ = "internal_emails"
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String(36), nullable=False, index=True)
    in_reply_to = Column(Integer, ForeignKey("internal_emails.id"), nullable=True)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    recipients = Column(JSON, nullable=False)
    subject = Column(String(500), nullable=False)
    body_html = Column(Text, nullable=True)
    body_text = Column(Text, nullable=True)
    attachments_json = Column(JSON, nullable=True)
    folder_id = Column(Integer, ForeignKey("email_folders.id"), nullable=True)
    labels = Column(JSON, nullable=True)
    is_read = Column(Boolean, default=False)
    is_starred = Column(Boolean, default=False)
    is_draft = Column(Boolean, default=False)
    is_external = Column(Boolean, default=False)
    external_message_id = Column(String(255), nullable=True)
    read_at = Column(DateTime, nullable=True)
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    
    sender = relationship("User", foreign_keys=[sender_id])
    reply_to = relationship("InternalEmail", remote_side=[id], backref="replies")
    folder = relationship("EmailFolder", backref="emails")

    __table_args__ = (
        Index("ix_email_thread", "thread_id", "created_at"),
        Index("ix_email_sender", "sender_id", "created_at"),
        Index("ix_email_folder", "folder_id", "is_read"),
    )


class ChatAttachment(Base):
    __tablename__ = "chat_attachments"
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, nullable=False, index=True)
    message_type = Column(String(30), nullable=False)
    media_asset_id = Column(Integer, ForeignKey("media_assets.id"), nullable=True)
    attachment_type = Column(String(20), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    waveform_json = Column(JSON, nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    is_processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    
    media_asset = relationship("MediaAsset", foreign_keys=[media_asset_id])

    __table_args__ = (
        Index("ix_chat_att_msg", "message_id", "message_type"),
        Index("ix_chat_att_type", "attachment_type"),
    )


class ChatReadReceipt(Base):
    __tablename__ = "chat_read_receipts"
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, nullable=False, index=True)
    message_type = Column(String(30), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    read_at = Column(DateTime, default=_utcnow)
    
    employee = relationship("Employee", backref="read_receipts")

    __table_args__ = (UniqueConstraint("message_id", "message_type", "employee_id", name="uq_chat_read_receipt"),)


class EmployeeActivityLog(Base):
    __tablename__ = "employee_activity_logs"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    actor_employee_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True)
    target_employee_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(Integer, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=True)
    ip_address = Column(String(45), nullable=True)
    device_fingerprint = Column(String(255), nullable=True)
    session_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=_utcnow, index=True)
    
    actor = relationship("Employee", back_populates="activity_logs", foreign_keys=[actor_employee_id])
    target = relationship("Employee", back_populates="activity_logs_targeted", foreign_keys=[target_employee_id])

    __table_args__ = (
        Index("ix_act_log_actor_time", "actor_employee_id", "created_at"),
        Index("ix_act_log_target", "target_employee_id"),
        Index("ix_act_log_action", "action", "created_at"),
        Index("ix_act_log_country", "country_code", "created_at"),
    )

