"""controllers.hr.employees_controller controller.

Business logic is delegated to services.hr.employees_controller_service (routers -> controllers -> services)."""

from domains.hr.services.employees_controller_service import (
    acknowledge_shift_handover, approve_work_log, check_in_employee, check_in_with_geo, check_out_employee, close_communication_channel,
    create_employee, create_employee_document, create_employee_relation, create_employee_role, create_leave_request, create_masked_communication_channel,
    create_office, create_shift_handover_channel, create_shift_roster, create_war_room_chat, create_work_log, delete_employee,
    delete_office, employee_payload, generate_email_alias, generate_meeting_token, generate_qr_login_token, get_employee,
    get_employee_communication_stats, get_shift_handover_summary, kill_switch, list_attendance, list_employee_documents, list_employee_relations,
    list_employee_roles, list_employees, list_offices, list_work_logs, remove_employee_relation, scan_outgoing_dlp,
    send_entity_chat_message, send_treasury_email, update_employee, update_employee_document_status, update_office, validate_geo_location,
    validate_qr_login
)

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
