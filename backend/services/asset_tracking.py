from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session

from models import EmployeeAsset, AuditLog
from utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)


class AssetTrackingService:
    """
    Asset lifecycle management from procurement to disposal.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def assign_asset(
        self,
        employee_id: int,
        asset_type: str,
        asset_tag: Optional[str] = None,
        serial_number: Optional[str] = None,
    ) -> EmployeeAsset:
        """Assign an asset to an employee."""
        asset = EmployeeAsset(
            employee_id=employee_id,
            asset_type=asset_type,
            asset_tag=asset_tag,
            serial_number=serial_number,
            assigned_at=_utcnow(),
            recovery_status="active",
        )
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        return asset
    
    def return_asset(self, asset_id: int, recovery_status: str = "recovered") -> bool:
        """Return an asset from an employee."""
        asset = (
            self.db.query(EmployeeAsset)
            .filter(EmployeeAsset.id == asset_id)
            .first()
        )
        if not asset:
            return False
        
        asset.returned_at = _utcnow()
        asset.recovery_status = recovery_status
        self.db.commit()
        return True
    
    def track_condition(self, asset_id: int, condition: str) -> None:
        """Update asset condition."""
        audit = AuditLog(
            event_type="asset_condition",
            actor_id=None,
            action="update",
            resource_type="asset",
            resource_id=asset_id,
            details={"condition": condition},
            occurred_at=_utcnow(),
        )
        self.db.add(audit)
        self.db.commit()
    
    def get_recovery_report(self) -> List[dict]:
        """Get report of assets pending recovery."""
        pending = (
            self.db.query(EmployeeAsset)
            .filter(
                EmployeeAsset.returned_at == None,
                EmployeeAsset.recovery_status != "active",
            )
            .all()
        )
        
        return [
            {
                "asset_id": a.id,
                "employee_id": a.employee_id,
                "asset_type": a.asset_type,
                "asset_tag": a.asset_tag,
                "recovery_status": a.recovery_status,
            }
            for a in pending
        ]

