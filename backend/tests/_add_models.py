with open('models/employee_models.py', 'r') as f:
    content = f.read()

old_end = '    country_code = Column(String(10), nullable=True, index=True)\n    \n    employee = relationship("Employee", foreign_keys=[employee_id])\n'

new_end = old_end + '''


class ChatAttachment(Base):
    __tablename__ = "chat_attachments"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, nullable=False, index=True)
    message_type = Column(String(20), nullable=False, default="direct")
    attachment_type = Column(String(20), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_name = Column(String(200), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    waveform_json = Column(Text, nullable=True)
    is_processed = Column(Boolean, default=False)


class InternalEmail(Base):
    __tablename__ = "internal_emails"
    __table_args__ = (
        Index("ix_internal_emails_thread_id", "thread_id"),
        Index("ix_internal_emails_sender_id", "sender_id"),
        Index("ix_internal_emails_folder_id", "folder_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String(200), nullable=False)
    body_html = Column(Text, nullable=True)
    body_text = Column(Text, nullable=True)
    recipients = Column(Text, nullable=True)
    thread_id = Column(String(64), nullable=True)
    is_external = Column(Boolean, default=False)
    external_message_id = Column(String(200), nullable=True)
    country_code = Column(String(10), nullable=True)
    folder_id = Column(Integer, ForeignKey("email_folders.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class EmailFolder(Base):
    __tablename__ = "email_folders"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    name = Column(String(50), nullable=False)
    folder_type = Column(String(20), default="inbox")
    is_system = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)'''

if old_end in content:
    content = content.replace(old_end, new_end, 1)
    with open('models/employee_models.py', 'w') as f:
        f.write(content)
    print('Added models')
else:
    print('Pattern not found')
    print(repr(content[-300:]))
