import json
import os
from datetime import timedelta
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from data.models import AuditLog, CampaignRecipient, ChatbotQueryEvent, RetentionJobRun, ShipmentEvent
from utils.datetime_utils import utcnow as _utcnow


_RETENTION_POLICIES = (
    {"target": "audit_logs", "model": AuditLog, "days": 365, "timestamp": "created_at"},
    {"target": "shipment_events", "model": ShipmentEvent, "days": 180, "timestamp": "created_at"},
    {"target": "campaign_recipients", "model": CampaignRecipient, "days": 180, "timestamp": "created_at"},
    {"target": "chatbot_query_events", "model": ChatbotQueryEvent, "days": 180, "timestamp": "created_at"},
)
_RETENTION_BATCH_SIZE = 1000
_RUN_INTERVAL = timedelta(hours=20)


def _artifact_root() -> Path:
    return Path(__file__).resolve().parents[2] / "artifacts" / "retention"


def _serialize_row(row: Any) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for column in row.__table__.columns:
        value = getattr(row, column.name)
        data[column.name] = value.isoformat() if hasattr(value, "isoformat") else value
    return data


def _should_skip_recent_run(target_name: str, db: Session) -> bool:
    latest_run = (
        db.query(RetentionJobRun)
        .filter(RetentionJobRun.target_name == target_name)
        .order_by(RetentionJobRun.started_at.desc())
        .first()
    )
    if latest_run is None:
        return False
    started_at = getattr(latest_run, "started_at", None)
    if started_at is None:
        return False
    return started_at >= _utcnow() - _RUN_INTERVAL


def run_operational_retention_cycle(db: Session) -> dict[str, Any]:
    delete_after_archive = os.getenv("ZOZI_RETENTION_DELETE_ARCHIVED", "0") == "1"
    artifact_root = _artifact_root()
    artifact_root.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    for policy in _RETENTION_POLICIES:
        target_name = str(policy["target"])
        if _should_skip_recent_run(target_name, db):
            results.append({"target": target_name, "status": "skipped_recent_run"})
            continue

        now = _utcnow()
        cutoff_days = int(policy["days"])
        cutoff = now - timedelta(days=cutoff_days)
        model = policy["model"]
        timestamp_column = getattr(model, str(policy["timestamp"]))
        rows = (
            db.query(model)
            .filter(timestamp_column < cutoff)
            .order_by(timestamp_column.asc())
            .limit(_RETENTION_BATCH_SIZE)
            .all()
        )

        artifact_path: str | None = None
        archived_count = 0
        deleted_count = 0
        status = "completed"
        if rows:
            artifact_file = artifact_root / f"{target_name}-{now.strftime('%Y%m%d%H%M%S')}.jsonl"
            with artifact_file.open("w", encoding="utf-8") as handle:
                for row in rows:
                    handle.write(json.dumps(_serialize_row(row), default=str) + "\n")
            artifact_path = str(artifact_file)
            archived_count = len(rows)
            if delete_after_archive:
                for row in rows:
                    db.delete(row)
                deleted_count = len(rows)
                status = "archived_and_deleted"

        run = RetentionJobRun(
            target_name=target_name,
            cutoff_days=cutoff_days,
            status=status,
            archived_count=archived_count,
            deleted_count=deleted_count,
            artifact_path=artifact_path,
            result_json=json.dumps(
                {
                    "cutoff": cutoff.isoformat(),
                    "batch_size": _RETENTION_BATCH_SIZE,
                    "delete_after_archive": delete_after_archive,
                },
                default=str,
            ),
            started_at=now,
            completed_at=_utcnow(),
        )
        db.add(run)
        db.flush()
        results.append(
            {
                "target": target_name,
                "status": status,
                "archived": archived_count,
                "deleted": deleted_count,
                "artifact_path": artifact_path,
                "run_id": getattr(run, "id", None),
            }
        )

    return {"targets": results, "delete_after_archive": delete_after_archive}

