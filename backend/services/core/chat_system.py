import logging
import secrets
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from data.models_core import DirectChatRoom, DirectChatMessage, GroupChatRoom, GroupChatMember, GroupChatMessage
from data.models import User, ChatAttachment
from services.storage import storage as _storage

logger = logging.getLogger("zozi.chat")


@dataclass
class ChatThread:
    thread_id: str
    entity_type: str
    entity_id: int
    participants: List[int] = field(default_factory=list)
    name: str = ""
    is_external: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    channel_type: str = "entity"


class ChatSystem:
    def __init__(self, db: Session):
        self.db = db

    def create_entity_chat(
        self,
        entity_type: str,
        entity_id: int,
        participants: List[int],
        name: Optional[str] = None,
        is_external: bool = False,
        country_code: Optional[str] = None,
    ) -> dict:
        from data.models_core import EntityChatThread
        thread = EntityChatThread(
            entity_type=entity_type,
            entity_id=entity_id,
            title=name or f"{entity_type.replace('_', ' ').title()} Chat",
        )
        self.db.add(thread)
        self.db.commit()
        self.db.refresh(thread)

        return {
            "thread_id": thread.id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "participants": participants,
            "name": thread.title,
            "is_external": is_external,
            "created_at": thread.created_at.isoformat(),
            "messages": [],
        }

    def create_direct_chat(
        self,
        participant_ids: List[int],
        employee_id: Optional[int] = None,
        country_code: Optional[str] = None,
    ) -> dict:
        if len(participant_ids) != 2:
            raise ValueError("Direct chat requires exactly 2 participants")

        p1, p2 = sorted(participant_ids)[0], sorted(participant_ids)[1]
        existing = self.db.query(DirectChatRoom).filter(
            DirectChatRoom.participant_one == p1,
            DirectChatRoom.participant_two == p2,
            DirectChatRoom.is_active == True,
        ).first()

        if existing:
            return {
                "chat_id": existing.chat_id,
                "type": "direct",
                "participants": [existing.participant_one, existing.participant_two],
                "created_at": existing.created_at.isoformat(),
            }

        chat_id = f"dm_{secrets.token_hex(8)}"
        room = DirectChatRoom(
            chat_id=chat_id,
            participant_one=p1,
            participant_two=p2,
            country_code=country_code,
            is_masked=employee_id not in participant_ids if employee_id else False,
            is_active=True,
        )
        self.db.add(room)
        self.db.commit()
        self.db.refresh(room)

        return {
            "chat_id": chat_id,
            "id": room.id,
            "type": "direct",
            "participants": [room.participant_one, room.participant_two],
            "created_by": employee_id,
            "country_code": country_code,
            "created_at": room.created_at.isoformat(),
            "is_masked": room.is_masked,
        }

    def create_group_chat(
        self,
        name: str,
        participant_ids: List[int],
        is_encrypted: bool = False,
        country_code: Optional[str] = None,
        created_by: Optional[int] = None,
    ) -> dict:
        chat_id = f"group_{secrets.token_hex(8)}"
        room = GroupChatRoom(
            chat_id=chat_id,
            name=name,
            country_code=country_code,
            is_encrypted=is_encrypted,
            created_by=created_by or 0,
            is_active=True,
        )
        self.db.add(room)
        self.db.flush()

        for uid in participant_ids:
            member = GroupChatMember(
                room_id=room.id,
                user_id=uid,
                role="admin" if uid == created_by else "member",
            )
            self.db.add(member)

        self.db.commit()
        self.db.refresh(room)

        return {
            "chat_id": chat_id,
            "name": name,
            "type": "group",
            "participants": participant_ids,
            "is_encrypted": is_encrypted,
            "created_by": created_by,
            "country_code": country_code,
            "created_at": room.created_at.isoformat(),
        }

    def send_message(
        self,
        chat_id: str,
        sender_id: int,
        content: str,
        message_type: str = "text",
    ) -> dict:
        chat_type = chat_id.split("_")[0] if "_" in chat_id else "dm"

        if chat_type == "dm" or chat_type == "direct":
            room = self.db.query(DirectChatRoom).filter(
                DirectChatRoom.chat_id == chat_id,
                DirectChatRoom.is_active == True,
            ).first()
            if not room:
                raise ValueError(f"Direct chat {chat_id} not found")
            msg = DirectChatMessage(
                room_id=room.id,
                sender_id=sender_id,
                message=content,
                message_type=message_type,
            )
        elif chat_type == "group":
            room = self.db.query(GroupChatRoom).filter(
                GroupChatRoom.chat_id == chat_id,
                GroupChatRoom.is_active == True,
            ).first()
            if not room:
                raise ValueError(f"Group chat {chat_id} not found")
            msg = GroupChatMessage(
                room_id=room.id,
                sender_id=sender_id,
                message=content,
                message_type=message_type,
            )
        else:
            from data.models_core import EntityChatThread, EntityChatMessage
            thread = self.db.query(EntityChatThread).filter(
                EntityChatThread.id == int(chat_id)
            ).first()
            if not thread:
                raise ValueError(f"Entity chat {chat_id} not found")
            msg = EntityChatMessage(
                thread_id=thread.id,
                sender_id=sender_id,
                message=content,
            )

        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)

        return {
            "id": msg.id,
            "chat_id": chat_id,
            "sender_id": sender_id,
            "content": content,
            "message_type": message_type,
            "created_at": msg.created_at.isoformat(),
        }

    def get_chat_history(self, chat_id: str, limit: int = 100) -> list:
        chat_type = chat_id.split("_")[0] if "_" in chat_id else "dm"
        if chat_type == "dm" or chat_type == "direct":
            room = self.db.query(DirectChatRoom).filter(
                DirectChatRoom.chat_id == chat_id
            ).first()
            if not room:
                return []
            messages = self.db.query(DirectChatMessage).filter(
                DirectChatMessage.room_id == room.id
            ).order_by(DirectChatMessage.created_at.desc()).limit(limit).all()
            return [
                {
                    "id": m.id,
                    "sender_id": m.sender_id,
                    "message": m.message,
                    "message_type": m.message_type,
                    "read_at": m.read_at.isoformat() if m.read_at else None,
                    "created_at": m.created_at.isoformat(),
                }
                for m in reversed(messages)
            ]
        elif chat_type == "group":
            room = self.db.query(GroupChatRoom).filter(
                GroupChatRoom.chat_id == chat_id
            ).first()
            if not room:
                return []
            messages = self.db.query(GroupChatMessage).filter(
                GroupChatMessage.room_id == room.id
            ).order_by(GroupChatMessage.created_at.desc()).limit(limit).all()
            return [
                {
                    "id": m.id,
                    "sender_id": m.sender_id,
                    "message": m.message,
                    "message_type": m.message_type,
                    "read_at": m.read_at.isoformat() if m.read_at else None,
                    "created_at": m.created_at.isoformat(),
                }
                for m in reversed(messages)
            ]
        return []

    async def send_message_with_files(
        self,
        chat_id: str,
        sender_id: int,
        content: str,
        files: list,
    ) -> dict:
        """Send a message with file attachments.
        Saves uploaded files to disk and creates ChatAttachment records.
        """
        import os
        from datetime import datetime, timezone

        # Resolve chat type — numeric IDs are entity/thread chats
        if chat_id.isdigit():
            chat_type = "entity"
        else:
            chat_type = chat_id.split("_")[0] if "_" in chat_id else "dm"

        now = datetime.now(timezone.utc)
        message_type = "text" if not files else "file"

        if chat_type == "entity":
            from data.models_core import EntityChatThread, EntityChatMessage
            thread = self.db.query(EntityChatThread).filter(
                EntityChatThread.id == int(chat_id)
            ).first()
            if not thread:
                raise ValueError(f"Entity chat {chat_id} not found")
            msg = EntityChatMessage(
                thread_id=thread.id,
                sender_id=sender_id,
                message=content or f"{len(files)} file(s)",
            )
        elif chat_type == "dm" or chat_type == "direct":
            from data.models_core import DirectChatRoom, DirectChatMessage
            room = self.db.query(DirectChatRoom).filter(
                DirectChatRoom.chat_id == chat_id,
                DirectChatRoom.is_active == True,
            ).first()
            if not room:
                raise ValueError(f"Direct chat {chat_id} not found")
            msg = DirectChatMessage(
                room_id=room.id,
                sender_id=sender_id,
                message=content or f"{len(files)} file(s)",
                message_type=message_type,
            )
        elif chat_type == "group":
            from data.models_core import GroupChatRoom, GroupChatMessage
            room = self.db.query(GroupChatRoom).filter(
                GroupChatRoom.chat_id == chat_id,
                GroupChatRoom.is_active == True,
            ).first()
            if not room:
                raise ValueError(f"Group chat {chat_id} not found")
            msg = GroupChatMessage(
                room_id=room.id,
                sender_id=sender_id,
                message=content or f"{len(files)} file(s)",
                message_type=message_type,
            )

        self.db.add(msg)
        self.db.flush()

        # Save files and create ChatAttachment records
        attachment_data = []
        for f in files:
            content_bytes = await f.read()
            key = f"chat/{msg.id}/{uuid.uuid4().hex}_{f.filename or 'untitled'}"
            url = _storage.save(key, content_bytes, content_type=f.content_type)

            # Determine attachment type from mime
            mime = f.content_type or "application/octet-stream"
            if mime.startswith("image/"):
                att_type = "image"
            elif mime.startswith("video/"):
                att_type = "video"
            elif mime == "application/pdf":
                att_type = "document"
            else:
                att_type = "file"

            attachment = ChatAttachment(
                message_id=msg.id,
                message_type=message_type,
                attachment_type=att_type,
                file_url=url,
                file_name=f.filename or "untitled",
                file_size_bytes=len(content_bytes),
                mime_type=mime,
                created_at=now,
            )
            self.db.add(attachment)
            self.db.flush()

            attachment_data.append({
                "id": attachment.id,
                "type": att_type,
                "file_name": attachment.file_name,
                "file_size": attachment.file_size_bytes,
                "file_url": attachment.file_url,
                "mime_type": attachment.mime_type,
            })

        self.db.commit()
        self.db.refresh(msg)

        return {
            "id": msg.id,
            "chat_id": chat_id,
            "sender_id": sender_id,
            "content": content,
            "message_type": message_type,
            "created_at": msg.created_at.isoformat(),
            "attachments": attachment_data,
        }

    def mark_read(
        self,
        chat_id: str,
        user_id: int,
    ) -> dict:
        """Mark all unread messages in a chat as read."""
        chat_type = chat_id.split("_")[0] if "_" in chat_id else "dm"
        now = datetime.now(timezone.utc)
        count = 0

        if chat_type == "dm" or chat_type == "direct":
            room = self.db.query(DirectChatRoom).filter(
                DirectChatRoom.chat_id == chat_id,
                DirectChatRoom.is_active == True,
            ).first()
            if not room:
                raise ValueError(f"Direct chat {chat_id} not found")
            messages = self.db.query(DirectChatMessage).filter(
                DirectChatMessage.room_id == room.id,
                DirectChatMessage.sender_id != user_id,
                DirectChatMessage.read_at.is_(None),
            ).all()
            for msg in messages:
                msg.read_at = now
                count += 1
        elif chat_type == "group":
            room = self.db.query(GroupChatRoom).filter(
                GroupChatRoom.chat_id == chat_id,
                GroupChatRoom.is_active == True,
            ).first()
            if not room:
                raise ValueError(f"Group chat {chat_id} not found")
            messages = self.db.query(GroupChatMessage).filter(
                GroupChatMessage.room_id == room.id,
                GroupChatMessage.sender_id != user_id,
                GroupChatMessage.read_at.is_(None),
            ).all()
            for msg in messages:
                msg.read_at = now
                count += 1
        else:
            from data.models_core import EntityChatMessage
            messages = self.db.query(EntityChatMessage).filter(
                EntityChatMessage.thread_id == int(chat_id),
                EntityChatMessage.sender_id != user_id,
                EntityChatMessage.read_at.is_(None),
            ).all()
            for msg in messages:
                msg.read_at = now
                count += 1

        self.db.commit()
        return {"chat_id": chat_id, "marked_read": count}

    def create_thread(self, title: str, entity_type: Optional[str] = None, entity_id: Optional[int] = None) -> dict:
        from data.models_core import EntityChatThread
        thread = EntityChatThread(
            title=title,
            entity_type=entity_type or "admin",
            entity_id=entity_id or 0,
        )
        self.db.add(thread)
        self.db.commit()
        self.db.refresh(thread)

        return {
            "id": thread.id,
            "title": thread.title,
            "entity_type": thread.entity_type,
            "entity_id": thread.entity_id,
            "is_direct": False,
            "created_at": thread.created_at.isoformat(),
        }

    def get_thread_messages(self, thread_id: int, limit: int = 50, cursor: Optional[int] = None) -> dict:
        """Get thread messages with cursor-based pagination.

        Returns:
            {
                "messages": [...],
                "has_more": bool,
                "next_cursor": int | None,
            }
        """
        from data.models_core import EntityChatThread, EntityChatMessage
        from data.models import User
        thread = self.db.query(EntityChatThread).filter(
            EntityChatThread.id == thread_id
        ).first()
        if not thread:
            return {"messages": [], "has_more": False, "next_cursor": None}

        query = (
            self.db.query(EntityChatMessage, User.full_name)
            .join(User, EntityChatMessage.sender_id == User.id)
            .filter(EntityChatMessage.thread_id == thread.id)
        )

        # Cursor: fetch messages with ID < cursor (messages before the cursor)
        if cursor is not None:
            query = query.filter(EntityChatMessage.id < cursor)

        # Fetch limit + 1 to determine has_more
        rows = (
            query
            .order_by(EntityChatMessage.created_at.desc(), EntityChatMessage.id.desc())
            .limit(limit + 1)
            .all()
        )

        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        messages = [
            {
                "id": m.EntityChatMessage.id,
                "sender_id": m.EntityChatMessage.sender_id,
                "sender_name": m.full_name or f"User {m.EntityChatMessage.sender_id}",
                "body": m.EntityChatMessage.message,
                "created_at": m.EntityChatMessage.created_at.isoformat(),
            }
            for m in reversed(rows)
        ]

        next_cursor = rows[0].EntityChatMessage.id if rows else None

        return {
            "messages": messages,
            "has_more": has_more,
            "next_cursor": next_cursor,
        }

    def list_threads(self) -> list:
        from data.models_core import EntityChatThread, EntityChatMessage
        from sqlalchemy import func, desc
        subq = (
            self.db.query(
                EntityChatMessage.thread_id,
                func.max(EntityChatMessage.created_at).label("last_msg_at"),
            )
            .group_by(EntityChatMessage.thread_id)
            .subquery()
        )
        last_msg = (
            self.db.query(
                EntityChatMessage.thread_id,
                EntityChatMessage.message,
            )
            .distinct(EntityChatMessage.thread_id)
            .order_by(
                EntityChatMessage.thread_id,
                EntityChatMessage.created_at.desc(),
            )
            .subquery()
        )
        threads = (
            self.db.query(EntityChatThread, subq.c.last_msg_at, last_msg.c.message)
            .outerjoin(subq, EntityChatThread.id == subq.c.thread_id)
            .outerjoin(last_msg, EntityChatThread.id == last_msg.c.thread_id)
            .filter(EntityChatThread.is_active == True)
            .order_by(desc(subq.c.last_msg_at))
            .limit(50)
            .all()
        )
        return [
            {
                "id": t.EntityChatThread.id,
                "entity_type": t.EntityChatThread.entity_type,
                "entity_id": t.EntityChatThread.entity_id,
                "title": t.EntityChatThread.title,
                "is_direct": False,
                "last_message_at": t.last_msg_at.isoformat() if t.last_msg_at else None,
                "last_message_preview": t.message[:80] if t.message else None,
                "unread_count": 0,
                "created_at": t.EntityChatThread.created_at.isoformat(),
            }
            for t in threads
        ]

    def get_chat_metrics(self) -> dict:
        from data.models_core import EntityChatThread, EntityChatMessage
        from sqlalchemy import func as sqlfunc

        total_threads = self.db.query(sqlfunc.count(EntityChatThread.id)).scalar() or 0
        total_messages = self.db.query(sqlfunc.count(EntityChatMessage.id)).scalar() or 0
        return {
            "total_threads": total_threads,
            "total_messages": total_messages,
        }


def get_chat_system(db: Session) -> ChatSystem:
    return ChatSystem(db)
