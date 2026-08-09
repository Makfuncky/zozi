"""Tests for internal email delivery and internal channels."""
from __future__ import annotations

import uuid
from datetime import date

import pytest

from models.communication import InternalEmail, EmailFolder
from data.models_employee_models import Employee
from data.models import User


@pytest.fixture
def admin_headers(client):
    email = f"commadmin_{uuid.uuid4().hex[:8]}@zozi.test"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": f"commadmin_{uuid.uuid4().hex[:8]}",
            "password": "SecurePass1!",
            "role": "admin",
        },
    )
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass1!"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, token


@pytest.fixture
def admin_token(admin_headers):
    return admin_headers[1]


@pytest.fixture
def recipient_id(db_session):
    email = f"recipient_{uuid.uuid4().hex[:8]}@zozi.test"
    user = User(email=email, username=f"recipient_{uuid.uuid4().hex[:8]}", hashed_password="hashed", role="employee")
    db_session.add(user)
    db_session.flush()
    emp = Employee(user_id=user.id, employee_code=f"EMP-{user.id}", employment_status="active", hire_date=date(2024, 1, 1))
    db_session.add(emp)
    db_session.flush()
    return user.id, emp.id


@pytest.mark.integration
def test_internal_email_stored_in_db(client, admin_token, recipient_id, db_session):
    recipient_user_id, recipient_emp_id = recipient_id
    resp = client.post(
        "/api/v1/email/internal",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "to": [recipient_user_id],
            "subject": "ZOZI Internal Update",
            "body": "Please review the attached communication policy.",
        },
    )
    assert resp.status_code in (200, 201), resp.text
    body = resp.json()
    assert body["status"] == "sent"
    assert body["delivered_count"] == 1
    assert body["sender_id"] is not None

    email = db_session.query(InternalEmail).filter(InternalEmail.sender_id == body["sender_id"]).first()
    assert email is not None
    assert email.subject == "ZOZI Internal Update"
    assert email.is_external is False
    assert email.thread_id is not None

    folder = db_session.query(EmailFolder).filter(EmailFolder.employee_id == recipient_emp_id, EmailFolder.name == "inbox").first()
    assert folder is not None
    assert folder.emails and folder.emails[0].id == email.id


@pytest.mark.integration
def test_internal_channels_crud(client, admin_token):
    sender_user_id = 1
    create = client.post(
        "/api/v1/internal-channels/channels",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "General",
            "description": "Company-wide updates",
            "is_public": True,
            "created_by": sender_user_id,
            "allowed_roles": ["admin", "employee"],
        },
    )
    assert create.status_code in (200, 201), create.text
    ch = create.json()
    assert ch["name"] == "General"
    channel_id = ch["channel_id"]

    listed = client.get("/api/v1/internal-channels/channels", params={"user_id": sender_user_id}, headers={"Authorization": f"Bearer {admin_token}"})
    assert listed.status_code == 200
    assert any(c["channel_id"] == channel_id for c in listed.json())

    msg = client.post(
        f"/api/v1/internal-channels/channels/{channel_id}/messages",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"sender_id": sender_user_id, "content": "Hello channel", "message_type": "text"},
    )
    assert msg.status_code in (200, 201), msg.text
    assert msg.json()["content"] == "Hello channel"
