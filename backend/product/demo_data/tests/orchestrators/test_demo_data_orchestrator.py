import pytest
from django.test import TestCase

from infra.authz.repositories.auth_repository import AuthRepository
from infra.authz.services.auth_service import AuthService
from infra.common.classes import MembershipRoles
from infra.common.exceptions import Conflict, Forbidden
from infra.tenants.dtos.dtos import TenantIn
from infra.tenants.entities.tenant_entities import TenantMembershipEntity
from infra.tenants.orchestrators.tenant_orchestrator import TenantOrchestrator
from infra.tenants.services.tenants_service import TenantService
from product.costing.services.costing_service import CostingService
from product.demo_data.orchestrators.demo_data_orchestrator import (
    DemoDataOrchestrator,
)
from product.timekeeping.services.timekeeping_service import TimekeepingService
from product.workforce.entities.workforce_entities import DepartmentEntity
from product.workforce.services.workforce_service import WorkforceService
from shared.audit.services.audit_service import AuditService


def make_user(email: str = "owner@example.com"):
    return AuthRepository.create_user(
        email=email,
        full_name="Test User",
        password_hash=AuthService._hash_password("SecurePass123!"),
    )


def make_tenant_with_owner(slug: str = "acme"):
    owner = make_user()
    tenant = TenantOrchestrator.create(
        TenantIn(name="Acme Corp", slug=slug), user_id=owner.id
    )
    return tenant, owner


class DemoDataOrchestratorSeedTests(TestCase):
    def test_seed_creates_all_categories(self):
        tenant, owner = make_tenant_with_owner()

        counts = DemoDataOrchestrator.seed(tenant.id, owner.id)

        assert counts["departments"] == 5
        assert counts["employees"] == 20
        assert counts["periods"] == 4
        assert counts["overtime_rules"] == 2
        assert counts["reports"] > 0
        assert counts["time_entries"] > 0

        assert len(WorkforceService.list_departments(tenant.id)) == 5
        assert len(WorkforceService.list_employees(tenant.id)) == 20
        assert len(TimekeepingService.list_periods(tenant.id, owner.id)) == 4
        assert len(CostingService.list_rules(tenant.id, owner.id)) == 2

    def test_seed_writes_one_summary_audit_event(self):
        tenant, owner = make_tenant_with_owner()

        DemoDataOrchestrator.seed(tenant.id, owner.id)

        events = AuditService.get_all(tenant.id, owner.id, action="demo_data.seeded")
        assert len(events) == 1
        assert events[0].resource_type == "Tenant"
        assert events[0].resource_id == tenant.id
        assert events[0].metadata["departments"] == 5
        assert events[0].metadata["employees"] == 20

    def test_seed_rejects_if_departments_exist(self):
        tenant, owner = make_tenant_with_owner()
        WorkforceService.create_department(
            tenant.id, DepartmentEntity(name="Pre-existing"), owner.id
        )

        with pytest.raises(Conflict, match="already has data"):
            DemoDataOrchestrator.seed(tenant.id, owner.id)

        assert len(WorkforceService.list_departments(tenant.id)) == 1
        assert len(WorkforceService.list_employees(tenant.id)) == 0

    def test_seed_rejects_non_owner(self):
        tenant, owner = make_tenant_with_owner()
        admin = make_user("admin@example.com")
        TenantService.add_membership(
            tenant_id=tenant.id,
            user_id=admin.id,
            entity=TenantMembershipEntity(role=MembershipRoles.ADMIN.value),
            invited_by_id=owner.id,
        )

        with pytest.raises(Forbidden):
            DemoDataOrchestrator.seed(tenant.id, admin.id)

        assert len(WorkforceService.list_departments(tenant.id)) == 0
