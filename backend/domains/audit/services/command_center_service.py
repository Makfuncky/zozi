"""Command Center view service."""

from sqlalchemy.orm import Session

from domains.audit.models.audit_schema_models import CommandCenterView


def list_command_center_views(db: Session, user_id: int) -> list[CommandCenterView]:
    return (
        db.query(CommandCenterView)
        .filter(CommandCenterView.user_id == user_id, CommandCenterView.is_deleted.is_(False))
        .order_by(CommandCenterView.is_default.desc(), CommandCenterView.created_at.desc())
        .all()
    )


def create_command_center_view(db: Session, user_id: int, view_name: str, config: dict, is_default: bool) -> CommandCenterView:
    if is_default:
        db.query(CommandCenterView).filter(
            CommandCenterView.user_id == user_id, CommandCenterView.is_default.is_(True)
        ).update({"is_default": False})
    view = CommandCenterView(user_id=user_id, view_name=view_name, config=config, is_default=is_default)
    db.add(view)
    db.commit()
    db.refresh(view)
    return view


def update_command_center_view(db: Session, view_id: int, user_id: int, view_name: str | None = None, config: dict | None = None, is_default: bool | None = None) -> CommandCenterView:
    view = db.get(CommandCenterView, view_id)
    if not view:
        raise ValueError("View not found")
    if view_name is not None:
        view.view_name = view_name
    if config is not None:
        view.config = config
    if is_default is not None and is_default:
        db.query(CommandCenterView).filter(
            CommandCenterView.user_id == user_id, CommandCenterView.id != view_id
        ).update({"is_default": False})
        view.is_default = True
    db.commit()
    db.refresh(view)
    return view


def delete_command_center_view(db: Session, view_id: int, user_id: int) -> None:
    view = db.get(CommandCenterView, view_id)
    if not view:
        raise ValueError("View not found")
    view.is_deleted = True
    db.commit()
