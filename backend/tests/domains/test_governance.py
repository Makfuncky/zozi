"""Domain tests for governance — workflow engine, admin operations, and audit."""
from __future__ import annotations

import pytest


class TestGovernanceServiceImports:
    """Smoke tests: verify governance service modules are importable."""

    def test_import_workflow_engine(self):
        from domains.governance.services import workflow_engine

        assert workflow_engine is not None

    def test_import_admin_service(self):
        from domains.governance.services.admin import admin_service

        assert admin_service is not None

    def test_import_audit_service(self):
        from domains.governance.services.audit import audit_service

        assert audit_service is not None

    def test_import_governance_models(self):
        from domains.governance.models.core import Workflow, Policy

        assert Workflow is not None
        assert Policy is not None

    def test_import_governance_ports(self):
        from domains.governance.ports import SystemSetting

        assert SystemSetting is not None

    def test_import_governance_features(self):
        from domains.governance.features import GOVERNANCE_FEATURES

        assert isinstance(GOVERNANCE_FEATURES, (list, tuple, set))


class TestWorkflowEngine:
    """Tests for workflow engine operations."""

    def test_workflow_engine_class(self):
        from domains.governance.services.workflow_engine import WorkflowEngine

        assert WorkflowEngine is not None
        assert hasattr(WorkflowEngine, "create_workflow")
        assert hasattr(WorkflowEngine, "execute_workflow")

    def test_workflow_status_enum(self):
        from domains.governance.services.workflow_engine import WorkflowStatus

        assert WorkflowStatus.DRAFT.value == "draft"
        assert WorkflowStatus.PENDING.value == "pending"
        assert WorkflowStatus.APPROVED.value == "approved"
        assert WorkflowStatus.REJECTED.value == "rejected"
        assert WorkflowStatus.ACTIVE.value == "active"
        assert WorkflowStatus.COMPLETED.value == "completed"
        assert WorkflowStatus.CANCELLED.value == "cancelled"

    def test_workflow_engine_create_workflow(self, db_session):
        from domains.governance.services.workflow_engine import WorkflowEngine

        engine = WorkflowEngine(db=db_session)
        result = engine.create_workflow(
            name="test_workflow",
            workflow_type="approval",
            steps=[{"name": "step1", "action": "approve"}],
        )

        assert result["name"] == "test_workflow"
        assert result["type"] == "approval"

    def test_workflow_engine_init(self, db_session):
        from domains.governance.services.workflow_engine import WorkflowEngine

        engine = WorkflowEngine(db=db_session)
        assert engine.db is db_session


class TestAdminOperations:
    """Tests for admin governance operations."""

    def test_admin_service_exists(self):
        from domains.governance.services.admin.admin_service import bulk_delete_users

        assert callable(bulk_delete_users)

    def test_governance_policies_exist(self):
        from domains.governance.policies.governance_policies import enforce_governance_policy

        assert callable(enforce_governance_policy)

    def test_audit_service_has_audit_log(self):
        from domains.governance.services.audit.audit_service import create_audit_log

        assert callable(create_audit_log)

    def test_governance_read_models(self):
        from domains.governance.read_models.governance_read_models import GovernanceReadModel

        assert GovernanceReadModel is not None
