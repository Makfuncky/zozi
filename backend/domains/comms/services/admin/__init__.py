"""Admin comms services."""
from sqlalchemy.orm import Session


def get_communication_audit_service(db: Session):
    raise NotImplementedError("Communication audit service is not yet implemented.")

