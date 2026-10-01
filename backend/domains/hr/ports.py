"""hr domain - sanctioned cross-domain READ surface (ports).

Per NEW_STRUCTURE.md Law 3, cross-domain *reads* may ONLY happen through a
publishing domain's ``ports.py``. Other domains import these functions instead
of importing ``domains.hr.models`` or ``domains.hr.services`` directly.

These are pure read helpers: no writes, no business decisions, no permission
checks (callers remain responsible for feature gating via ``rbac``).
"""


from typing import List, Optional

from sqlalchemy.orm import Session

from infrastructure.utils.pagination import (
    CursorPage,
    MAX_PAGE_SIZE,
    cursor_paginate_asc,
)

# --- Keyset (cursor) pagination helpers (diagram §6: NEVER OFFSET on hot lists) ---
# The existing ``list_*`` functions keep their public contract (a plain ``List``)
# so cross-domain consumers are unaffected, but they are now sourced via keyset
# (stable ``id`` order, no OFFSET). The ``*_page`` companions return a ``CursorPage``
# for scale-ready cursor paging (the 100Ks-concurrent-user path).

def _keyset_list(model, db: Session, limit: int = 100) -> list:
    """Backward-compatible plain list sourced via keyset (no OFFSET)."""
    return cursor_paginate_asc(db.query(model), page_size=limit).items


def _keyset_page(model, db: Session, cursor: Optional[str] = None,
                 page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page over ``model`` (scale-ready, no OFFSET)."""
    return cursor_paginate_asc(db.query(model), cursor=cursor, page_size=page_size)

from domains.hr.models.employee_models import AlumniNetwork, COIReport, DisciplinaryCase, DynamicQRSession, Employee, EmployeeActivityLog, EmployeeAddress, EmployeeAsset, EmployeeAttendance, EmployeeBiometric, EmployeeCertification, EmployeeDependent, EmployeeDocument, EmployeeLeaveLedger, EmployeeLeaveRequest, EmployeeRelation, EmployeeRiskScore, EmployeeRole, EmployeeShiftRoster, EmployeeTraining, EmployeeWorkLog, GeoFenceLog, OffboardingCase, Office, OrgUnit, PayrollRecord, PhysicalIDCard, TrainingModule, TravelRequest
from domains.hr.models.hr_schema_models import OnboardingPipeline, OnboardingStep  # A3: sanctioned ports surface for accounts hub
from domains.hr.models.employee_models import ShiftHandoverTask
# TODO: payroll_engine not yet created
# from domains.hr.services.payroll_engine import PayrollEngine


def get_office_by_id(db: Session, id_: int) -> Optional[Office]:
    """Return Office by primary key (or None)."""
    return db.get(Office, id_)

def list_offices(db: Session, limit: int = 100) -> List[Office]:
    """Return up to ``limit`` Office rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Office, db, limit)

def list_offices_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of Office rows (scale-ready)."""
    return _keyset_page(Office, db, cursor, page_size)

def get_physical_id_card_by_id(db: Session, id_: int) -> Optional[PhysicalIDCard]:
    """Return PhysicalIDCard by primary key (or None)."""
    return db.get(PhysicalIDCard, id_)

def list_physical_id_cards(db: Session, limit: int = 100) -> List[PhysicalIDCard]:
    """Return up to ``limit`` PhysicalIDCard rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(PhysicalIDCard, db, limit)

def list_physical_id_cards_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of PhysicalIDCard rows (scale-ready)."""
    return _keyset_page(PhysicalIDCard, db, cursor, page_size)

def get_dynamic_qr_session_by_id(db: Session, id_: int) -> Optional[DynamicQRSession]:
    """Return DynamicQRSession by primary key (or None)."""
    return db.get(DynamicQRSession, id_)

def list_dynamic_qr_sessions(db: Session, limit: int = 100) -> List[DynamicQRSession]:
    """Return up to ``limit`` DynamicQRSession rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(DynamicQRSession, db, limit)

def list_dynamic_q_r_sessions_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of DynamicQRSession rows (scale-ready)."""
    return _keyset_page(DynamicQRSession, db, cursor, page_size)

def get_employee_biometric_by_id(db: Session, id_: int) -> Optional[EmployeeBiometric]:
    """Return EmployeeBiometric by primary key (or None)."""
    return db.get(EmployeeBiometric, id_)

def list_employee_biometrics(db: Session, limit: int = 100) -> List[EmployeeBiometric]:
    """Return up to ``limit`` EmployeeBiometric rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EmployeeBiometric, db, limit)

def list_employee_biometrics_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of EmployeeBiometric rows (scale-ready)."""
    return _keyset_page(EmployeeBiometric, db, cursor, page_size)

def get_geo_fence_log_by_id(db: Session, id_: int) -> Optional[GeoFenceLog]:
    """Return GeoFenceLog by primary key (or None)."""
    return db.get(GeoFenceLog, id_)

def list_geo_fence_logs(db: Session, limit: int = 100) -> List[GeoFenceLog]:
    """Return up to ``limit`` GeoFenceLog rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(GeoFenceLog, db, limit)

def list_geo_fence_logs_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of GeoFenceLog rows (scale-ready)."""
    return _keyset_page(GeoFenceLog, db, cursor, page_size)

def get_employee_role_by_id(db: Session, id_: int) -> Optional[EmployeeRole]:
    """Return EmployeeRole by primary key (or None)."""
    return db.get(EmployeeRole, id_)

def list_employee_roles(db: Session, limit: int = 100) -> List[EmployeeRole]:
    """Return up to ``limit`` EmployeeRole rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EmployeeRole, db, limit)

def list_employee_roles_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of EmployeeRole rows (scale-ready)."""
    return _keyset_page(EmployeeRole, db, cursor, page_size)

def get_org_unit_by_id(db: Session, id_: int) -> Optional[OrgUnit]:
    """Return OrgUnit by primary key (or None)."""
    return db.get(OrgUnit, id_)

def list_org_units(db: Session, limit: int = 100) -> List[OrgUnit]:
    """Return up to ``limit`` OrgUnit rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(OrgUnit, db, limit)

def list_org_units_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of OrgUnit rows (scale-ready)."""
    return _keyset_page(OrgUnit, db, cursor, page_size)

def get_employee_by_id(db: Session, id_: int) -> Optional[Employee]:
    """Return Employee by primary key (or None)."""
    return db.get(Employee, id_)

def list_employees(db: Session, limit: int = 100) -> List[Employee]:
    """Return up to ``limit`` Employee rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Employee, db, limit)

def list_employees_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of Employee rows (scale-ready)."""
    return _keyset_page(Employee, db, cursor, page_size)

def get_employee_attendance_by_id(db: Session, id_: int) -> Optional[EmployeeAttendance]:
    """Return EmployeeAttendance by primary key (or None)."""
    return db.get(EmployeeAttendance, id_)

def list_employee_attendances(db: Session, limit: int = 100) -> List[EmployeeAttendance]:
    """Return up to ``limit`` EmployeeAttendance rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EmployeeAttendance, db, limit)

def list_employee_attendances_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of EmployeeAttendance rows (scale-ready)."""
    return _keyset_page(EmployeeAttendance, db, cursor, page_size)

def get_employee_work_log_by_id(db: Session, id_: int) -> Optional[EmployeeWorkLog]:
    """Return EmployeeWorkLog by primary key (or None)."""
    return db.get(EmployeeWorkLog, id_)

def list_employee_work_logs(db: Session, limit: int = 100) -> List[EmployeeWorkLog]:
    """Return up to ``limit`` EmployeeWorkLog rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EmployeeWorkLog, db, limit)

def list_employee_work_logs_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of EmployeeWorkLog rows (scale-ready)."""
    return _keyset_page(EmployeeWorkLog, db, cursor, page_size)

def get_employee_leave_request_by_id(db: Session, id_: int) -> Optional[EmployeeLeaveRequest]:
    """Return EmployeeLeaveRequest by primary key (or None)."""
    return db.get(EmployeeLeaveRequest, id_)

def list_employee_leave_requests(db: Session, limit: int = 100) -> List[EmployeeLeaveRequest]:
    """Return up to ``limit`` EmployeeLeaveRequest rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EmployeeLeaveRequest, db, limit)

def list_employee_leave_requests_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of EmployeeLeaveRequest rows (scale-ready)."""
    return _keyset_page(EmployeeLeaveRequest, db, cursor, page_size)

def get_employee_leave_ledger_by_id(db: Session, id_: int) -> Optional[EmployeeLeaveLedger]:
    """Return EmployeeLeaveLedger by primary key (or None)."""
    return db.get(EmployeeLeaveLedger, id_)

def list_employee_leave_ledgers(db: Session, limit: int = 100) -> List[EmployeeLeaveLedger]:
    """Return up to ``limit`` EmployeeLeaveLedger rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EmployeeLeaveLedger, db, limit)

def list_employee_leave_ledgers_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of EmployeeLeaveLedger rows (scale-ready)."""
    return _keyset_page(EmployeeLeaveLedger, db, cursor, page_size)

def get_employee_shift_roster_by_id(db: Session, id_: int) -> Optional[EmployeeShiftRoster]:
    """Return EmployeeShiftRoster by primary key (or None)."""
    return db.get(EmployeeShiftRoster, id_)

def list_employee_shift_rosters(db: Session, limit: int = 100) -> List[EmployeeShiftRoster]:
    """Return up to ``limit`` EmployeeShiftRoster rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EmployeeShiftRoster, db, limit)

def list_employee_shift_rosters_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of EmployeeShiftRoster rows (scale-ready)."""
    return _keyset_page(EmployeeShiftRoster, db, cursor, page_size)

def get_employee_asset_by_id(db: Session, id_: int) -> Optional[EmployeeAsset]:
    """Return EmployeeAsset by primary key (or None)."""
    return db.get(EmployeeAsset, id_)

def list_employee_assets(db: Session, limit: int = 100) -> List[EmployeeAsset]:
    """Return up to ``limit`` EmployeeAsset rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EmployeeAsset, db, limit)

def list_employee_assets_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of EmployeeAsset rows (scale-ready)."""
    return _keyset_page(EmployeeAsset, db, cursor, page_size)

def get_employee_certification_by_id(db: Session, id_: int) -> Optional[EmployeeCertification]:
    """Return EmployeeCertification by primary key (or None)."""
    return db.get(EmployeeCertification, id_)

def list_employee_certifications(db: Session, limit: int = 100) -> List[EmployeeCertification]:
    """Return up to ``limit`` EmployeeCertification rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EmployeeCertification, db, limit)

def list_employee_certifications_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of EmployeeCertification rows (scale-ready)."""
    return _keyset_page(EmployeeCertification, db, cursor, page_size)

def get_employee_document_by_id(db: Session, id_: int) -> Optional[EmployeeDocument]:
    """Return EmployeeDocument by primary key (or None)."""
    return db.get(EmployeeDocument, id_)

def list_employee_documents(db: Session, limit: int = 100) -> List[EmployeeDocument]:
    """Return up to ``limit`` EmployeeDocument rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EmployeeDocument, db, limit)

def list_employee_documents_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of EmployeeDocument rows (scale-ready)."""
    return _keyset_page(EmployeeDocument, db, cursor, page_size)

def get_employee_dependent_by_id(db: Session, id_: int) -> Optional[EmployeeDependent]:
    """Return EmployeeDependent by primary key (or None)."""
    return db.get(EmployeeDependent, id_)

def list_employee_dependents(db: Session, limit: int = 100) -> List[EmployeeDependent]:
    """Return up to ``limit`` EmployeeDependent rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EmployeeDependent, db, limit)

def list_employee_dependents_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of EmployeeDependent rows (scale-ready)."""
    return _keyset_page(EmployeeDependent, db, cursor, page_size)

def get_employee_relation_by_id(db: Session, id_: int) -> Optional[EmployeeRelation]:
    """Return EmployeeRelation by primary key (or None)."""
    return db.get(EmployeeRelation, id_)

def list_employee_relations(db: Session, limit: int = 100) -> List[EmployeeRelation]:
    """Return up to ``limit`` EmployeeRelation rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EmployeeRelation, db, limit)

def list_employee_relations_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of EmployeeRelation rows (scale-ready)."""
    return _keyset_page(EmployeeRelation, db, cursor, page_size)

def get_employee_address_by_id(db: Session, id_: int) -> Optional[EmployeeAddress]:
    """Return EmployeeAddress by primary key (or None)."""
    return db.get(EmployeeAddress, id_)

def list_employee_addresses(db: Session, limit: int = 100) -> List[EmployeeAddress]:
    """Return up to ``limit`` EmployeeAddress rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EmployeeAddress, db, limit)

def list_employee_addresses_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of EmployeeAddress rows (scale-ready)."""
    return _keyset_page(EmployeeAddress, db, cursor, page_size)

def get_c_o_i_report_by_id(db: Session, id_: int) -> Optional[COIReport]:
    """Return COIReport by primary key (or None)."""
    return db.get(COIReport, id_)

def list_coi_reports(db: Session, limit: int = 100) -> List[COIReport]:
    """Return up to ``limit`` COIReport rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(COIReport, db, limit)

def list_c_o_i_reports_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of COIReport rows (scale-ready)."""
    return _keyset_page(COIReport, db, cursor, page_size)

def get_travel_request_by_id(db: Session, id_: int) -> Optional[TravelRequest]:
    """Return TravelRequest by primary key (or None)."""
    return db.get(TravelRequest, id_)

def list_travel_requests(db: Session, limit: int = 100) -> List[TravelRequest]:
    """Return up to ``limit`` TravelRequest rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(TravelRequest, db, limit)

def list_travel_requests_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of TravelRequest rows (scale-ready)."""
    return _keyset_page(TravelRequest, db, cursor, page_size)

# --- OnboardingPipeline / OnboardingStep (moved from accounts god-module, A3) ---

def get_onboarding_pipeline_by_id(db: Session, id_: int) -> Optional[OnboardingPipeline]:
    """Return OnboardingPipeline by primary key (or None)."""
    return db.get(OnboardingPipeline, id_)

def list_onboarding_pipelines(db: Session, limit: int = 100) -> List[OnboardingPipeline]:
    """Return up to ``limit`` OnboardingPipeline rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(OnboardingPipeline, db, limit)

def list_onboarding_pipelines_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of onboarding pipelines (scale-ready)."""
    return _keyset_page(OnboardingPipeline, db, cursor, page_size)


def get_onboarding_step_by_id(db: Session, id_: int) -> Optional[OnboardingStep]:
    """Return OnboardingStep by primary key (or None)."""
    return db.get(OnboardingStep, id_)

def list_onboarding_steps(db: Session, limit: int = 100) -> List[OnboardingStep]:
    """Return up to ``limit`` OnboardingStep rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(OnboardingStep, db, limit)

def list_onboarding_steps_page(
    db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE
) -> CursorPage:
    """Keyset-cursor page of onboarding steps (scale-ready)."""
    return _keyset_page(OnboardingStep, db, cursor, page_size)


# --- Model class references (for column access in cross-domain filters) ---
# These return the model class itself so cross-domain services can reference
# columns (e.g., ``employee_model().id == X``) without importing the model.

def employee_model() -> type:
    """Return the ``Employee`` model class (for column reference only)."""
    return Employee


def office_model() -> type:
    """Return the ``Office`` model class (for column reference only)."""
    return Office


def geo_fence_log_model() -> type:
    """Return the ``GeoFenceLog`` model class (for column reference only)."""
    return GeoFenceLog


def dynamic_qr_session_model() -> type:
    """Return the ``DynamicQRSession`` model class (for column reference only)."""
    return DynamicQRSession


def get_alumni_network_by_id(db: Session, id_: int) -> Optional[AlumniNetwork]:
    """Return AlumniNetwork by primary key (or None)."""
    return db.get(AlumniNetwork, id_)

def list_alumni_networks(db: Session, limit: int = 100) -> List[AlumniNetwork]:
    """Return up to ``limit`` AlumniNetwork rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(AlumniNetwork, db, limit)

def list_alumni_networks_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of AlumniNetwork rows (scale-ready)."""
    return _keyset_page(AlumniNetwork, db, cursor, page_size)

def get_disciplinary_case_by_id(db: Session, id_: int) -> Optional[DisciplinaryCase]:
    """Return DisciplinaryCase by primary key (or None)."""
    return db.get(DisciplinaryCase, id_)

def list_disciplinary_cases(db: Session, limit: int = 100) -> List[DisciplinaryCase]:
    """Return up to ``limit`` DisciplinaryCase rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(DisciplinaryCase, db, limit)

def list_disciplinary_cases_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of DisciplinaryCase rows (scale-ready)."""
    return _keyset_page(DisciplinaryCase, db, cursor, page_size)

def get_offboarding_case_by_id(db: Session, id_: int) -> Optional[OffboardingCase]:
    """Return OffboardingCase by primary key (or None)."""
    return db.get(OffboardingCase, id_)

def list_offboarding_cases(db: Session, limit: int = 100) -> List[OffboardingCase]:
    """Return up to ``limit`` OffboardingCase rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(OffboardingCase, db, limit)

def list_offboarding_cases_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of OffboardingCase rows (scale-ready)."""
    return _keyset_page(OffboardingCase, db, cursor, page_size)

def get_employee_risk_score_by_id(db: Session, id_: int) -> Optional[EmployeeRiskScore]:
    """Return EmployeeRiskScore by primary key (or None)."""
    return db.get(EmployeeRiskScore, id_)

def list_employee_risk_scores(db: Session, limit: int = 100) -> List[EmployeeRiskScore]:
    """Return up to ``limit`` EmployeeRiskScore rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EmployeeRiskScore, db, limit)

def list_employee_risk_scores_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of EmployeeRiskScore rows (scale-ready)."""
    return _keyset_page(EmployeeRiskScore, db, cursor, page_size)

def get_payroll_record_by_id(db: Session, id_: int) -> Optional[PayrollRecord]:
    """Return PayrollRecord by primary key (or None)."""
    return db.get(PayrollRecord, id_)

def list_payroll_records(db: Session, limit: int = 100) -> List[PayrollRecord]:
    """Return up to ``limit`` PayrollRecord rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(PayrollRecord, db, limit)

def list_payroll_records_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of PayrollRecord rows (scale-ready)."""
    return _keyset_page(PayrollRecord, db, cursor, page_size)

def get_training_module_by_id(db: Session, id_: int) -> Optional[TrainingModule]:
    """Return TrainingModule by primary key (or None)."""
    return db.get(TrainingModule, id_)

def list_training_modules(db: Session, limit: int = 100) -> List[TrainingModule]:
    """Return up to ``limit`` TrainingModule rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(TrainingModule, db, limit)

def list_training_modules_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of TrainingModule rows (scale-ready)."""
    return _keyset_page(TrainingModule, db, cursor, page_size)

def get_employee_training_by_id(db: Session, id_: int) -> Optional[EmployeeTraining]:
    """Return EmployeeTraining by primary key (or None)."""
    return db.get(EmployeeTraining, id_)

def list_employee_trainings(db: Session, limit: int = 100) -> List[EmployeeTraining]:
    """Return up to ``limit`` EmployeeTraining rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EmployeeTraining, db, limit)

def list_employee_trainings_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of EmployeeTraining rows (scale-ready)."""
    return _keyset_page(EmployeeTraining, db, cursor, page_size)

def get_employee_activity_log_by_id(db: Session, id_: int) -> Optional[EmployeeActivityLog]:
    """Return EmployeeActivityLog by primary key (or None)."""
    return db.get(EmployeeActivityLog, id_)

def list_employee_activity_logs(db: Session, limit: int = 100) -> List[EmployeeActivityLog]:
    """Return up to ``limit`` EmployeeActivityLog rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EmployeeActivityLog, db, limit)

def list_employee_activity_logs_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of EmployeeActivityLog rows (scale-ready)."""
    return _keyset_page(EmployeeActivityLog, db, cursor, page_size)


# ── Filtered read helpers (router-layer consolidation, ED3) ──────────
# These express the exact filters the employee routers previously ran inline
# so callers stay free of raw ``db.query`` in the module layer.


def get_employee_by_user_id(db: Session, user_id: int) -> Optional[Employee]:
    """Return the Employee whose ``user_id`` matches (or None)."""
    return db.query(Employee).filter(Employee.user_id == user_id).first()


def list_employee_documents_by_employee(
    db: Session, employee_id: int, doc_type: Optional[str] = None
) -> List[EmployeeDocument]:
    """Return EmployeeDocuments for an employee, newest first."""
    query = db.query(EmployeeDocument).filter(
        EmployeeDocument.employee_id == employee_id
    )
    if doc_type is not None:
        query = query.filter(EmployeeDocument.doc_type == doc_type)
    return query.order_by(EmployeeDocument.created_at.desc()).all()


def list_employee_relations_for_employee(
    db: Session, employee_id: int
) -> List[EmployeeRelation]:
    """Return EmployeeRelations where ``employee_id`` or ``internal_employee_id``
    matches (the COI conflict-of-interest join)."""
    from sqlalchemy import or_

    return (
        db.query(EmployeeRelation)
        .filter(
            or_(
                EmployeeRelation.employee_id == employee_id,
                EmployeeRelation.internal_employee_id == employee_id,
            )
        )
        .all()
    )


def list_active_org_units(
    db: Session, country_code: Optional[str] = None
) -> List[OrgUnit]:
    """Return active OrgUnits (optionally country-scoped), ordered by path/name."""
    query = db.query(OrgUnit).filter(OrgUnit.is_active == True)  # noqa: E712
    if country_code:
        query = query.filter(OrgUnit.country_code == country_code)
    return query.order_by(OrgUnit.path, OrgUnit.name).all()

# NOTE: The following imports were removed because the functions don't exist:
# - can_manage, backfill_authority_levels, reassign_manager
# These were undefined in hierarchy_service (pre-existing bug).
# from domains.hr.services.hierarchy_service import can_manage
# from domains.hr.services.hierarchy_service import backfill_authority_levels, reassign_manager
# TODO: Module not yet created
# from domains.hr.services.leave_accrual import LeaveAccrualEngine


# ── ESS service functions (sanctioned cross-domain delegation) ──────────────
# Thin wrappers so module routers import from hr.ports instead of
# directly from domains.hr.services.ess_service.

def get_employee_profile(db: Session, employee_id: int) -> dict:
    """Sanctioned cross-domain read: get employee profile."""
    from domains.hr.services.ess_service import get_employee_profile as _svc
    return _svc(db, employee_id)


def update_employee_profile(
    db: Session, employee_id: int,
    phone: Optional[str] = None, address: Optional[str] = None,
    emergency_contact_name: Optional[str] = None, emergency_contact_phone: Optional[str] = None,
) -> dict:
    """Sanctioned cross-domain write: update employee profile."""
    from domains.hr.services.ess_service import update_employee_profile as _svc
    return _svc(db, employee_id, phone=phone, address=address,
                emergency_contact_name=emergency_contact_name,
                emergency_contact_phone=emergency_contact_phone)


def get_leave_balance(db: Session, employee_id: int) -> List[dict]:
    """Sanctioned cross-domain read: get leave balance."""
    from domains.hr.services.ess_service import get_leave_balance as _svc
    return _svc(db, employee_id)


def create_leave_request(db: Session, employee_id: int, leave_type: str, start_date: str, end_date: str, reason: str) -> dict:
    """Sanctioned cross-domain write: create leave request."""
    from domains.hr.services.ess_service import create_leave_request as _svc
    return _svc(db, employee_id, leave_type, start_date, end_date, reason)


def get_leave_history(db: Session, employee_id: int) -> List[dict]:
    """Sanctioned cross-domain read: get leave history."""
    from domains.hr.services.ess_service import get_leave_history as _svc
    return _svc(db, employee_id)


def get_payslips(db: Session, employee_id: int) -> List[dict]:
    """Sanctioned cross-domain read: get payslips."""
    from domains.hr.services.ess_service import get_payslips as _svc
    return _svc(db, employee_id)


def get_attendance(db: Session, employee_id: int) -> List[dict]:
    """Sanctioned cross-domain read: get attendance."""
    from domains.hr.services.ess_service import get_attendance as _svc
    return _svc(db, employee_id)


def get_okrs(db: Session, employee_id: int) -> List[dict]:
    """Sanctioned cross-domain read: get OKRs."""
    from domains.hr.services.ess_service import get_okrs as _svc
    return _svc(db, employee_id)


def get_org_chart(db: Session, org_unit_id: Optional[int], employee_id: int) -> dict:
    """Sanctioned cross-domain read: get org chart."""
    from domains.hr.services.ess_service import get_org_chart as _svc
    return _svc(db, org_unit_id, employee_id)


def get_hr_employee_service(db: Session):
    """Sanctioned cross-domain factory: get HR employee service."""
    from domains.hr.services.hr_employee_service import get_hr_employee_service as _svc
    return _svc(db)


def get_travel_service(db: Session = None):
    """Sanctioned cross-domain factory: get travel service."""
    from domains.hr.services.travel.travel_service import get_travel_service as _svc
    return _svc(db)


def HREmployeeService(db: Session):
    """Sanctioned cross-domain factory: get HR employee service instance."""
    from domains.hr.services.hr_employee_service import HREmployeeService as _Cls
    return _Cls(db)


def PayrollEngine(db: Session = None, *args, **kwargs):
    """Sanctioned cross-domain factory: get PayrollEngine instance."""
    from domains.hr.services.payroll.payroll_engine import PayrollEngine as _Cls
    return _Cls(db, *args, **kwargs)

# --- Lazy service exports (Law 3 sanctioned cross-domain surface) ---
# Cross-domain consumers import these from ports instead of reaching
# into the services tree directly.
_LAZY_SERVICE_EXPORTS: dict[str, tuple[str, str]] = {
    "log_comm_event": ("domains.hr.services.employee_communication_service", "log_comm_event"),
    "get_all_subordinates": ("domains.hr.services.hierarchy.hierarchy_service", "get_all_subordinates"),
    "get_authority_level": ("domains.hr.services.hierarchy.hierarchy_service", "get_authority_level"),
    "get_user_chain": ("domains.hr.services.hierarchy.hierarchy_service", "get_user_chain"),
    "backfill_authority_levels": ("domains.hr.services.hierarchy.hierarchy_service", "backfill_authority_levels"),
    "can_manage": ("domains.hr.services.hierarchy.hierarchy_service", "can_manage"),
    "get_home_org_unit": ("domains.hr.services.hierarchy.hierarchy_service", "get_home_org_unit"),
    "get_org_chart": ("domains.hr.services.hierarchy.hierarchy_service", "get_org_chart"),
    "get_team_members": ("domains.hr.services.hierarchy.hierarchy_service", "get_team_members"),
    "is_in_chain": ("domains.hr.services.hierarchy.hierarchy_service", "is_in_chain"),
    "reassign_manager": ("domains.hr.services.hierarchy.hierarchy_service", "reassign_manager"),
    "PayrollEngine": ("domains.hr.services.payroll.payroll_engine", "PayrollEngine"),
}
import importlib

def __getattr__(name: str):
    if name in _LAZY_SERVICE_EXPORTS:
        module_path, symbol = _LAZY_SERVICE_EXPORTS[name]
        mod = importlib.import_module(module_path)
        value = getattr(mod, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# imports merged from services/
from typing import List, Optional
from sqlalchemy.orm import Session
from .events import HREvent  # noqa: F401 — re-export for type hints

# functions merged from services/
def _get_models():
    from domains.hr.models.employee_models import Employee
    from domains.hr.models.employee_models import EmployeeAttendance
    from domains.hr.models.employee_models import EmployeeLeaveRequest
    from domains.hr.models.employee_models import EmployeeDocument
    from domains.hr.models.employee_models import OrgUnit
    from domains.hr.models.employee_models import Office
    return Employee, EmployeeAttendance, EmployeeLeaveRequest, EmployeeDocument, OrgUnit, Office
