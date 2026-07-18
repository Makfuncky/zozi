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
    "OrgUnit"
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
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    parent_id = Column(Integer, ForeignKey("org_units.id"), nullable=True)
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
    reporting_manager_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    hiring_manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    authority_level = Column(Integer, nullable=True)
    org_unit_id = Column(Integer, ForeignKey("org_units.id"), nullable=True)
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
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    related_person_name = Column(String(160), nullable=False)
    relation_type = Column(String(30), nullable=False)
    is_internal_employee = Column(Boolean, default=False)
    internal_employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
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

