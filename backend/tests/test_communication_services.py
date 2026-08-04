"""Service-layer tests for internal communication, email gateway, and audit trail."""

import uuid
from datetime import date

import pytest

from data.models import User
from data.models_employee_models import Employee
from data.models_communication import EmailFolder, InternalEmail, ChatAttachment
from data.services_employee_communication_service import (
    get_or_create_direct_room,
    send_chat_message,
    get_chat_history,
    mark_message_read,
    send_internal_email,
    get_inbox,
    get_thread,
    get_employee_directory,
    _resolve_attachments,
)
from data.services_email_gateway import EmailGateway
from data.services_communication_audit import get_communication_audit_service


@pytest.fixture
def employee_pair(db_session):
    email_a = f"emp_a_{uuid.uuid4().hex[:8]}@zozi.test"
    email_b = f"emp_b_{uuid.uuid4().hex[:8]}@zozi.test"
    user_a = User(email=email_a, username=f"emp_a_{uuid.uuid4().hex[:8]}", hashed_password="hashed", role="employee")
    user_b = User(email=email_b, username=f"emp_b_{uuid.uuid4().hex[:8]}", hashed_password="hashed", role="employee")
    db_session.add_all([user_a, user_b])
    db_session.flush()
    emp_a = Employee(user_id=user_a.id, employee_code=f"EMP-A-{user_a.id}", employment_status="active", hire_date=date(2024, 1, 1))
    emp_b = Employee(user_id=user_b.id, employee_code=f"EMP-B-{user_b.id}", employment_status="active", hire_date=date(2024, 1, 1))
    db_session.add_all([emp_a, emp_b])
    db_session.flush()
    return user_a.id, user_b.id, emp_a.id, emp_b.id


@pytest.fixture
def sender_and_recipient(db_session):
    email_s = f"sender_{uuid.uuid4().hex[:8]}@zozi.test"
    email_r = f"recipient_{uuid.uuid4().hex[:8]}@zozi.test"
    user_s = User(email=email_s, username=f"sender_{uuid.uuid4().hex[:8]}", hashed_password="hashed", role="employee")
    user_r = User(email=email_r, username=f"recipient_{uuid.uuid4().hex[:8]}", hashed_password="hashed", role="employee")
    db_session.add_all([user_s, user_r])
    db_session.flush()
    emp_s = Employee(user_id=user_s.id, employee_code=f"EMP-S-{user_s.id}", employment_status="active", hire_date=date(2024, 1, 1))
    emp_r = Employee(user_id=user_r.id, employee_code=f"EMP-R-{user_r.id}", employment_status="active", hire_date=date(2024, 1, 1))
    db_session.add_all([emp_s, emp_r])
    db_session.flush()
    return user_s.id, user_r.id, emp_s.id, emp_r.id


def test_get_or_create_direct_room(db_session, employee_pair):
    user_a_id, user_b_id, emp_a_id, emp_b_id = employee_pair
    room_id = get_or_create_direct_room(db_session, emp_a_id, emp_b_id)
    assert isinstance(room_id, int)
    assert room_id > 0


def test_send_chat_message(db_session, employee_pair):
    user_a_id, user_b_id, emp_a_id, emp_b_id = employee_pair
    result = send_chat_message(db_session, sender_id=emp_a_id, receiver_id=emp_b_id, body="Hello service")
    assert result["id"] is not None
    assert result["body"] == "Hello service"


def test_get_chat_history(db_session, employee_pair):
    user_a_id, user_b_id, emp_a_id, emp_b_id = employee_pair
    send_result = send_chat_message(db_session, sender_id=emp_a_id, receiver_id=emp_b_id, body="History test")
    history = get_chat_history(db_session, room_id=send_result["room_id"], limit=10)
    assert len(history) >= 1


def test_send_internal_email_creates_records(db_session, sender_and_recipient):
    user_s_id, user_r_id, emp_s_id, emp_r_id = sender_and_recipient
    result = send_internal_email(
        db_session,
        sender_id=user_s_id,
        recipient_ids=[user_r_id],
        subject="Service Test",
        body_html="<p>Hello</p>",
    )
    assert result["id"] is not None
    assert result["thread_id"] is not None

    email = db_session.query(InternalEmail).filter(InternalEmail.id == result["id"]).first()
    assert email is not None
    assert email.subject == "Service Test"
    assert email.is_external is False

    folder = db_session.query(EmailFolder).filter(EmailFolder.employee_id == emp_r_id, EmailFolder.name == "inbox").first()
    assert folder is not None


def test_get_inbox_returns_emails(db_session, sender_and_recipient):
    user_s_id, user_r_id, emp_s_id, emp_r_id = sender_and_recipient
    send_internal_email(db_session, sender_id=user_s_id, recipient_ids=[user_r_id], subject="Inbox Test", body_html="<p>Body</p>")
    inbox = get_inbox(db_session, employee_id=emp_r_id, folder="inbox", limit=10, offset=0)
    assert inbox["total"] >= 1
    assert any(e["subject"] == "Inbox Test" for e in inbox["emails"])


def test_get_thread_returns_messages(db_session, sender_and_recipient):
    user_s_id, user_r_id, emp_s_id, emp_r_id = sender_and_recipient
    send_internal_email(db_session, sender_id=user_s_id, recipient_ids=[user_r_id], subject="Thread Test", body_html="<p>Body</p>")
    thread_id = db_session.query(InternalEmail).filter(InternalEmail.sender_id == user_s_id).first().thread_id
    messages = get_thread(db_session, thread_id=thread_id)
    assert len(messages) >= 1
    assert messages[0]["subject"] == "Thread Test"


def test_get_employee_directory(db_session, sender_and_recipient):
    user_s_id, user_r_id, emp_s_id, emp_r_id = sender_and_recipient
    results = get_employee_directory(db_session, limit=10)
    assert len(results) >= 2
    ids = [r["id"] for r in results]
    assert emp_s_id in ids
    assert emp_r_id in ids


def test_mark_message_read(db_session, employee_pair):
    user_a_id, user_b_id, emp_a_id, emp_b_id = employee_pair
    result = send_chat_message(db_session, sender_id=emp_a_id, receiver_id=emp_b_id, body="Read test")
    read_result = mark_message_read(db_session, message_id=result["id"], employee_id=emp_b_id, message_type="direct")
    assert read_result["status"] == "read"


def test_resolve_attachments_maps_columns(db_session):
    attachment = ChatAttachment(
        message_id=1,
        message_type="direct",
        attachment_type="image",
        file_url="http://example.com/img.png",
        file_name="img.png",
        file_size_bytes=1024,
        mime_type="image/png",
    )
    db_session.add(attachment)
    db_session.flush()
    resolved = _resolve_attachments(db_session, [attachment.id])
    assert len(resolved) == 1
    assert resolved[0]["file_name"] == "img.png"
    assert resolved[0]["attachment_type"] == "image"


def test_email_gateway_send_internal(db_session, sender_and_recipient):
    user_s_id, user_r_id, emp_s_id, emp_r_id = sender_and_recipient
    gateway = EmailGateway(db_session)
    result = gateway.send_internal_email(to_user_ids=[user_r_id], subject="Gateway Test", body="Body", sender_id=user_s_id)
    assert result["status"] == "sent"
    assert result["delivered_count"] == 1


def test_email_gateway_dlp_blocks_external(db_session):
    gateway = EmailGateway(db_session)
    result = gateway.send_external_email(to_email="external@example.com", subject="DLP", body="Credit card 4111 1111 1111 1111", sender_id=1)
    assert result["status"] == "blocked"
    assert "dlp_findings" in result


def test_communication_audit_log_and_query(db_session):
    service = get_communication_audit_service(db_session)
    logged = service.log_event(action="email_sent", channel="internal_email", content_preview="test", user_id=None, entity_type="internal_email", entity_id=0)
    assert logged["action"] == "email_sent"
    assert logged["channel"] == "internal_email"

    trail = service.get_audit_trail(limit=10)
    assert len(trail) >= 1
    assert trail[0]["action"] == "email_sent"
