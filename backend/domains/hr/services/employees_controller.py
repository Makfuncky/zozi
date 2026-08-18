"""controllers.hr.employees_controller controller.

Business logic is delegated to services.hr.employees_controller_service (routers -> controllers -> services)."""

from domains.hr.services.employees_controller_service import acknowledge_shift_handover
from domains.hr.services.employees_controller_service import approve_work_log
from domains.hr.services.employees_controller_service import check_in_employee
from domains.hr.services.employees_controller_service import check_in_with_geo
from domains.hr.services.employees_controller_service import check_out_employee
from domains.hr.services.employees_controller_service import close_communication_channel
from domains.hr.services.employees_controller_service import create_employee
from domains.hr.services.employees_controller_service import create_employee_document
from domains.hr.services.employees_controller_service import create_employee_relation
from domains.hr.services.employees_controller_service import create_employee_role
from domains.hr.services.employees_controller_service import create_leave_request
from domains.hr.services.employees_controller_service import create_masked_communication_channel
from domains.hr.services.employees_controller_service import create_office
from domains.hr.services.employees_controller_service import create_shift_handover_channel
from domains.hr.services.employees_controller_service import create_shift_roster
from domains.hr.services.employees_controller_service import create_war_room_chat
from domains.hr.services.employees_controller_service import create_work_log
from domains.hr.services.employees_controller_service import delete_employee
from domains.hr.services.employees_controller_service import delete_office
from domains.hr.services.employees_controller_service import employee_payload
from domains.hr.services.employees_controller_service import generate_email_alias
from domains.hr.services.employees_controller_service import generate_meeting_token
from domains.hr.services.employees_controller_service import generate_qr_login_token
from domains.hr.services.employees_controller_service import get_employee
from domains.hr.services.employees_controller_service import get_employee_communication_stats
from domains.hr.services.employees_controller_service import get_shift_handover_summary
from domains.hr.services.employees_controller_service import kill_switch
from domains.hr.services.employees_controller_service import list_attendance
from domains.hr.services.employees_controller_service import list_employee_documents
from domains.hr.services.employees_controller_service import list_employee_relations
from domains.hr.services.employees_controller_service import list_employee_roles
from domains.hr.services.employees_controller_service import list_employees
from domains.hr.services.employees_controller_service import list_offices
from domains.hr.services.employees_controller_service import list_work_logs
from domains.hr.services.employees_controller_service import remove_employee_relation
from domains.hr.services.employees_controller_service import scan_outgoing_dlp
from domains.hr.services.employees_controller_service import send_entity_chat_message
from domains.hr.services.employees_controller_service import send_treasury_email
from domains.hr.services.employees_controller_service import update_employee
from domains.hr.services.employees_controller_service import update_employee_document_status
from domains.hr.services.employees_controller_service import update_office
from domains.hr.services.employees_controller_service import validate_geo_location
from domains.hr.services.employees_controller_service import validate_qr_login

__all__ = [
    "acknowledge_shift_handover", "approve_work_log", "check_in_employee", "check_in_with_geo", "check_out_employee", "close_communication_channel",
    "create_employee", "create_employee_document", "create_employee_relation", "create_employee_role", "create_leave_request", "create_masked_communication_channel",
    "create_office", "create_shift_handover_channel", "create_shift_roster", "create_war_room_chat", "create_work_log", "delete_employee",
    "delete_office", "employee_payload", "generate_email_alias", "generate_meeting_token", "generate_qr_login_token", "get_employee",
    "get_employee_communication_stats", "get_shift_handover_summary", "kill_switch", "list_attendance", "list_employee_documents", "list_employee_relations",
    "list_employee_roles", "list_employees", "list_offices", "list_work_logs", "remove_employee_relation", "scan_outgoing_dlp",
    "send_entity_chat_message", "send_treasury_email", "update_employee", "update_employee_document_status", "update_office", "validate_geo_location",
    "validate_qr_login"
]
