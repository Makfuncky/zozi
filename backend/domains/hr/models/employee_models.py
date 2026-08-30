"""Employee models for HCM system."""
from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, Float, ForeignKey, Index, Integer, JSON, Numeric, String, Text, UniqueConstraint, Time, func
from sqlalchemy.orm import relationship
from . import Base
from domains.country.models.countries import CountryConfig  # noqa: F401
from infrastructure.utils.datetime_utils import utcnow as _utcnow

if TYPE_CHECKING:
    from . import User

__all__ = [
    "Office", "PhysicalIDCard", "DynamicQRSession", "EmployeeBiometric",
    "GeoFenceLog", "EmployeeRole", "Employee", "EmployeeAttendance",
    "EmployeeWorkLog", "EmployeeLeaveRequest", "EmployeeLeaveLedger", "EmployeeShiftRoster",
    "EmployeeAddress", "EmployeeDependent", "EmployeeAsset",
    "EmployeeCertification", "EmployeeDocument", "EmployeeRelation",
    "COIReport", "TravelRequest", "AlumniNetwork", "DisciplinaryCase", "OffboardingCase",
    "OrgUnit", "EmployeeActivityLog", "ShiftHandoverSession", "ShiftHandoverTask"
]


class Office(Base):
    __tablename__ = "offices"
    __table_args__ = {"schema": "hr"}
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    city = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    geo_fence_radius_meters = Column(Integer, default=100)
    address = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    country_code = Column(String(2), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)


class PhysicalIDCard(Base):
    __tablename__ = "physical_id_cards"
    __table_args__ = {"schema": "hr"}
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="SET NULL"), unique=True, nullable=False)
    card_number = Column(String(50), unique=True, nullable=False, index=True)
    issued_at = Column(DateTime, default=_utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)

    employee = relationship("Employee", back_populates="id_card")


class DynamicQRSession(Base):
    __tablename__ = "dynamic_qr_sessions"
    __table_args__ = {"schema": "hr"}
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="SET NULL"), nullable=False)
    qr_token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    device_fingerprint = Column(String(255), nullable=True)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)

    employee = relationship("Employee", back_populates="dynamic_qr_sessions")
    __table_args__ = (Index("ix_qr_session_employee_expires", "employee_id", "expires_at"), {"schema": "hr"})


class EmployeeBiometric(Base):
    __tablename__ = "employee_biometrics"
    __table_args__ = {"schema": "hr"}
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="SET NULL"), unique=True, nullable=False)
    fingerprint_hash = Column(String(255), nullable=True)
    face_encoding = Column(Text, nullable=True)
    biometric_type = Column(String(20), default="fingerprint")
    enrolled_at = Column(DateTime, default=_utcnow)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    country_code = Column(String(2), nullable=True, index=True)
    
    employee = relationship("Employee", back_populates="biometrics")


class GeoFenceLog(Base):
    __tablename__ = "geo_fence_logs"
    __table_args__ = {"schema": "hr"}
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="SET NULL"), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    accuracy_meters = Column(Integer, nullable=True)
    scanned_at = Column(DateTime, default=_utcnow)
    is_within_fence = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    country_code = Column(String(2), nullable=True, index=True)
    
    employee = relationship("Employee", back_populates="geo_fence_logs")


class EmployeeRole(Base):
    __tablename__ = "employee_roles"
    __table_args__ = {"schema": "hr"}
    id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(100), unique=True)
    permissions = Column(JSON)
    authority_level = Column(Integer, nullable=True)
    can_approve_leave = Column(Boolean, default=False)
    can_approve_expense = Column(Boolean, default=False)
    can_manage_users = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    country_code = Column(String(2), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)


class OrgUnit(Base):
    __tablename__ = "org_units"
    __table_args__ = {"schema": "hr"}
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    parent_id = Column(Integer, ForeignKey("hr.org_units.id", ondelete="SET NULL"), nullable=True)
    country_code = Column(String(2), nullable=True)
    level = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    parent = relationship("OrgUnit", remote_side=[id], backref="children")


class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = (
        UniqueConstraint("employee_code", name="uq_employees_code"),
        Index("ix_employees_user_id", "user_id"),
        Index("ix_employees_office", "office_id"), {"schema": "hr"})
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="CASCADE"), unique=True)
    employee_code = Column(String(20), unique=True, nullable=False)
    office_id = Column(Integer, ForeignKey("hr.offices.id", ondelete="SET NULL"), nullable=True)
    department = Column(String(100), nullable=True)
    position = Column(String(100), nullable=True)
    employment_type = Column(String(30), default="full_time")
    employment_status = Column(String(30), default="active")
    salary = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(3), default="OMR")
    country_code = Column(String(2), ForeignKey("country.country_configs.code", ondelete="SET NULL"), nullable=True)
    hire_date = Column(Date, nullable=False)
    termination_date = Column(Date, nullable=True)
    is_verified = Column(Boolean, default=False)
    gender = Column(String(20), nullable=True)
    years_of_experience = Column(Integer, nullable=True)
    performance_score = Column(Integer, nullable=True)
    education_level = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    reporting_manager_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="SET NULL"), nullable=True)
    hiring_manager_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)
    authority_level = Column(Integer, nullable=True)
    org_unit_id = Column(Integer, ForeignKey("hr.org_units.id", ondelete="SET NULL"), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    
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
    __tablename__ = "employee_attendances"
    __table_args__ = {"schema": "hr"}
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="CASCADE"), nullable=False, index=True)
    record_date = Column(Date, nullable=False)
    scan_in_time = Column(DateTime, nullable=True)
    scan_out_time = Column(DateTime, nullable=True)
    scan_type = Column(String(20), nullable=True)
    location_lat = Column(Float, nullable=True)
    location_long = Column(Float, nullable=True)
    device_fingerprint = Column(String(255), nullable=True)
    is_anomaly = Column(Boolean, default=False)
    status = Column(String(20), default="present")
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)
    
    employee = relationship("Employee", back_populates="attendance")
    
    __table_args__ = (UniqueConstraint("employee_id", "record_date", name="uq_attendance_employee_date"), CheckConstraint("status IN ('present', 'absent', 'late', 'half_day', 'on_leave', 'holiday')", name="chk_employee_attendance_status_valid"), {"schema": "hr"})


class EmployeeWorkLog(Base):
    __tablename__ = "employee_work_logs"
    __table_args__ = {"schema": "hr"}
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="CASCADE"), nullable=False, index=True)
    record_date = Column(Date, nullable=False)
    hours_worked = Column(Numeric(5, 2), default=0)
    task_description = Column(Text, nullable=True)
    location_lat = Column(Float, nullable=True)
    location_long = Column(Float, nullable=True)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)
    
    employee = relationship("Employee", back_populates="work_logs")


class EmployeeLeaveRequest(Base):
    __tablename__ = "employee_leave_requests"
    __table_args__ = {"schema": "hr"}
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="CASCADE"), nullable=False, index=True)
    leave_type = Column(String(50), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days_requested = Column(Integer, nullable=False)
    status = Column(String(20), default="pending")
    approved_by_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)
    
    employee = relationship("Employee", back_populates="leave_requests")
    approver = relationship("User", foreign_keys=[approved_by_id])

    __table_args__ = (CheckConstraint("status IN ('pending', 'approved', 'rejected', 'cancelled', 'withdrawn')", name="chk_employee_leave_requests_status_valid"), {"schema": "hr"})


class EmployeeLeaveLedger(Base):
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
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)
    
    employee = relationship("Employee", back_populates="leave_ledgers")


class EmployeeShiftRoster(Base):
    __tablename__ = "employee_shift_rosters"
    __table_args__ = {"schema": "hr"}
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="CASCADE"), nullable=False, index=True)
    shift_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    shift_type = Column(String(30), default="scheduled")
    status = Column(String(20), default="scheduled")
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)
    
    employee = relationship("Employee", back_populates="shift_rosters")
    
    __table_args__ = (UniqueConstraint("employee_id", "shift_date", name="uq_shift_employee_date"), CheckConstraint("status IN ('scheduled', 'confirmed', 'in_progress', 'completed', 'cancelled', 'swapped')", name="chk_employee_shift_rosters_status_valid"), {"schema": "hr"})


class EmployeeAsset(Base):
    __tablename__ = "employee_assets"
    __table_args__ = {"schema": "hr"}
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_type = Column(String(50), nullable=False)
    asset_id = Column(String(100), nullable=False)
    serial_no = Column(String(100), nullable=True)
    assigned_at = Column(DateTime, default=_utcnow)
    returned_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="assigned")
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)
    
    employee = relationship("Employee", back_populates="assets")

    __table_args__ = (CheckConstraint("status IN ('assigned', 'returned', 'lost', 'damaged', 'retired')", name="chk_employee_assets_status_valid"), {"schema": "hr"})


class EmployeeCertification(Base):
    __tablename__ = "employee_certifications"
    __table_args__ = {"schema": "hr"}
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="CASCADE"), nullable=False, index=True)
    cert_type = Column(String(100), nullable=False)
    cert_name = Column(String(200), nullable=False)
    issued_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    is_valid = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)
    
    employee = relationship("Employee", back_populates="certifications")


class EmployeeDocument(Base):
    __tablename__ = "employee_documents"
    __table_args__ = {"schema": "hr"}
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="CASCADE"), nullable=False, index=True)
    doc_type = Column(String(50), nullable=False)
    file_url = Column(String(500), nullable=False)
    expiry_date = Column(Date, nullable=True)
    verified_by_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)
    
    employee = relationship("Employee", back_populates="documents")
    verifier = relationship("User", foreign_keys=[verified_by_id])


class EmployeeDependent(Base):
    __tablename__ = "employee_dependents"
    __table_args__ = {"schema": "hr"}
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(160), nullable=False)
    relation = Column(String(50), nullable=False)
    dob = Column(Date, nullable=True)
    is_insured = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)
    
    employee = relationship("Employee", back_populates="dependents")


class EmployeeRelation(Base):
    __tablename__ = "employee_relations"
    __table_args__ = {"schema": "hr"}
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="CASCADE"), nullable=False, index=True)
    related_person_name = Column(String(160), nullable=False)
    relation_type = Column(String(30), nullable=False)
    is_internal_employee = Column(Boolean, default=False)
    internal_employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="SET NULL"), nullable=True)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)
    
    employee = relationship("Employee", back_populates="relations", foreign_keys=[employee_id])
    internal_employee = relationship("Employee", foreign_keys=[internal_employee_id])


class EmployeeAddress(Base):
    __tablename__ = "employee_addresses"
    __table_args__ = {"schema": "hr"}
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="CASCADE"), nullable=False, index=True)
    address_type = Column(String(30), nullable=False)
    street = Column(String(200), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country_code = Column(String(2), ForeignKey("country.country_configs.code", ondelete="SET NULL"), nullable=False)
    is_primary = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    
    employee = relationship("Employee", back_populates="addresses")
    country = relationship("CountryConfig", foreign_keys=[country_code])


class COIReport(Base):
    __tablename__ = "coi_reports"
    __table_args__ = {"schema": "hr"}
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="SET NULL"), nullable=False)
    related_person_name = Column(String(160), nullable=False)
    relation_type = Column(String(30), nullable=False)
    is_internal = Column(Boolean, default=False)
    internal_employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="SET NULL"), nullable=True)
    risk_level = Column(String(20), default="low")
    is_approved = Column(Boolean, default=False)
    approved_by_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)
    employee = relationship("Employee", foreign_keys=[employee_id], backref="coi_reports")
    internal_employee = relationship("Employee", foreign_keys=[internal_employee_id])
    approver = relationship("User", foreign_keys=[approved_by_id])


class TravelRequest(Base):
    __tablename__ = "employee_travel_requests"
    __table_args__ = {"schema": "hr"}
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="SET NULL"), nullable=False)
    destination_country = Column(String(2), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    purpose = Column(String(200), nullable=True)
    status = Column(String(20), default="pending")
    approved_by_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    per_diem_json = Column(JSON, nullable=True)
    total_cost = Column(Numeric(12, 2), nullable=True)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)
    
    employee = relationship("Employee", backref="travel_requests")
    approver = relationship("User", foreign_keys=[approved_by_id])

    __table_args__ = (CheckConstraint("status IN ('pending', 'approved', 'rejected', 'cancelled', 'completed')", name="chk_employee_travel_requests_status_valid"), {"schema": "hr"})


class AlumniNetwork(Base):
    __tablename__ = "alumni_networks"
    __table_args__ = {"schema": "hr"}
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="SET NULL"), unique=True, nullable=False)
    status = Column(String(20), default="active")
    granted_at = Column(DateTime, default=_utcnow)
    eligibility_expires_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)
    
    employee = relationship("Employee", backref="alumni_record")

    __table_args__ = (CheckConstraint("status IN ('active', 'inactive', 'suspended', 'graduated')", name="chk_alumni_network_status_valid"), {"schema": "hr"})

class DisciplinaryCase(Base):
    __tablename__ = "disciplinary_cases"
    __table_args__ = {"schema": "hr"}
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="SET NULL"), nullable=False, index=True)
    employee_name = Column(String(200), nullable=True)
    stage = Column(String(30), nullable=False, default="verbal_warning")
    description = Column(Text, nullable=False)
    issued_at = Column(DateTime, default=_utcnow)
    status = Column(String(20), default="active")
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)
 
    employee = relationship("Employee", foreign_keys=[employee_id], backref="disciplinary_cases")

    __table_args__ = (CheckConstraint("status IN ('active', 'resolved', 'escalated', 'closed', 'dismissed')", name="chk_disciplinary_cases_status_valid"), {"schema": "hr"})

class OffboardingCase(Base):
    __tablename__ = "offboarding_cases"
    __table_args__ = {"schema": "hr"}
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="SET NULL"), nullable=False, index=True)
    employee_name = Column(String(200), nullable=True)
    reason = Column(String(50), nullable=False, default="resignation")
    status = Column(String(20), default="pending")
    initiated_at = Column(DateTime, default=_utcnow)
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)
    
    employee = relationship("Employee", foreign_keys=[employee_id], backref="offboarding_cases")

    __table_args__ = (CheckConstraint("status IN ('pending', 'in_progress', 'completed', 'cancelled')", name="chk_offboarding_cases_status_valid"), {"schema": "hr"})


class EmployeeRiskScore(Base):
    __tablename__ = 'employee_risk_scores'
    __table_args__ = {"schema": "hr"}
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey('hr.employees.id', ondelete="SET NULL"), nullable=False, index=True)
    assessment_date = Column(Date, nullable=False)
    score = Column(Float, default=0.0)
    risk_level = Column(String(20), nullable=True)
    factors = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    country_code = Column(String(2), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)


class PayrollRecord(Base):
    __tablename__ = 'payroll_records'
    __table_args__ = {"schema": "hr"}
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(2), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey('hr.employees.id', ondelete="SET NULL"), nullable=True)
    net_pay = Column(Numeric(14, 2), default=0)
    status = Column(String(20), default='pending')
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')", name="chk_payroll_records_status_valid"),)


class TrainingModule(Base):
    __tablename__ = 'training_modules'
    __table_args__ = {"schema": "hr"}
    module_id = Column(String(36), primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    required_for_role = Column(String(50), nullable=True)
    duration_minutes = Column(Integer, default=30)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)


class EmployeeTraining(Base):
    __tablename__ = 'employee_trainings'
    __table_args__ = {"schema": "hr"}
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey('hr.employees.id', ondelete="SET NULL"), nullable=False, index=True)
    module_id = Column(String(36), ForeignKey('hr.training_modules.module_id', ondelete="SET NULL"), nullable=False)
    status = Column(String(20), default='assigned')
    score = Column(Float, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    __table_args__ = (
        CheckConstraint("status IN ('assigned', 'in_progress', 'completed', 'failed', 'expired')", name="chk_employee_trainings_status_valid"),)


class EmployeeActivityLog(Base):
    """Append-only audit trail of privileged/administrative employee actions.

    Written by ``services.security.auth_service._log_activity`` so security-relevant
    actions (logins, approvals, RLS context changes) are recorded even when the
    surrounding transaction rolls back.
    """
    __tablename__ = "employee_activity_logs"
    __table_args__ = {"schema": "hr"}
    id = Column(Integer, primary_key=True, index=True)
    actor_employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="SET NULL"), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(100), nullable=True)
    entity_id = Column(Integer, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    device_fingerprint = Column(String(255), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    employee = relationship("Employee", foreign_keys=[actor_employee_id], backref="activity_logs")


class ShiftHandoverSession(Base):
    __tablename__ = "shift_handover_sessions"
    __table_args__ = (
        Index("ix_handover_outgoing", "outgoing_employee_id"),
        Index("ix_handover_incoming", "incoming_employee_id"),
        Index("ix_handover_status", "status"),
        CheckConstraint("status IN ('pending', 'in_progress', 'completed', 'cancelled')", name="chk_shift_handover_sessions_status_valid"), {"schema": "hr"})
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(2), ForeignKey("country.country_configs.code", ondelete="SET NULL"), nullable=True)
    outgoing_employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="SET NULL"), nullable=False)
    incoming_employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="SET NULL"), nullable=True)
    shift_date = Column(DateTime, nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(String(20), default="pending")
    acknowledged_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    tasks = relationship("ShiftHandoverTask", back_populates="session", cascade="all, delete-orphan")


class ShiftHandoverTask(Base):
    __tablename__ = "shift_handover_tasks"
    __table_args__ = (
        CheckConstraint("status IN ('open', 'in_progress', 'completed', 'cancelled', 'blocked')", name="chk_shift_handover_tasks_status_valid"),
        {"extend_existing": True, "schema": "hr"},)
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("hr.shift_handover_sessions.id", ondelete="SET NULL"), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(20), default="normal")
    status = Column(String(20), default="open")
    assigned_to_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    session = relationship("ShiftHandoverSession", back_populates="tasks")


