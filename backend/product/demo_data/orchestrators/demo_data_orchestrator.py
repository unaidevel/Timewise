from datetime import date, timedelta
from decimal import Decimal
from random import Random

from django.db import transaction
from faker import Faker

from infra.common.exceptions import Conflict
from infra.tenants.decorators import only_owner
from product.costing.entities.costing_entities import OvertimeRuleEntity
from product.costing.services.costing_service import CostingService
from product.timekeeping.entities.timekeeping_entities import (
    PeriodEntity,
    TimeEntryEntity,
    TimeReportEntity,
)
from product.timekeeping.services.timekeeping_service import TimekeepingService
from product.workforce.dtos.dtos import EmployeeOut, RoleOut
from product.workforce.entities.workforce_entities import (
    CreateEmployeeEntity,
    DepartmentEntity,
)
from product.workforce.services.workforce_service import WorkforceService
from shared.audit.dtos.dtos import AuditEventIn
from shared.audit.services.audit_service import AuditService
from shared.audit.utils import AuditOutcome

DEPARTMENT_NAMES = ["Engineering", "Sales", "Operations", "Marketing", "Support"]
EMPLOYEE_COUNT = 20
PAST_PERIODS = 3
ACTIVE_PERIOD_DAYS = 30
REPORTS_PER_PAST_PERIOD = 6
ENTRIES_PER_REPORT_MIN = 5
ENTRIES_PER_REPORT_MAX = 10


class DemoDataOrchestrator:
    @only_owner
    @staticmethod
    def seed(tenant_id: int, user_id: int) -> dict[str, int]:
        if WorkforceService.list_departments(tenant_id):
            raise Conflict("Tenant already has data; demo seed refused.")
        if WorkforceService.list_employees(tenant_id):
            raise Conflict("Tenant already has data; demo seed refused.")

        fake = Faker("en_US")
        fake.unique.clear()
        rng = Random(42)

        with transaction.atomic():
            counts = _seed_all(tenant_id, user_id, fake, rng)

            AuditService.create(
                tenant_id,
                AuditEventIn(
                    action="demo_data.seeded",
                    resource_type="Tenant",
                    outcome=AuditOutcome.SUCCESS.value,
                    resource_id=tenant_id,
                    metadata=dict(counts),
                ),
                user_id,
            )

        return counts


def _seed_all(tenant_id: int, user_id: int, fake: Faker, rng: Random) -> dict[str, int]:
    departments = _seed_departments(tenant_id, user_id)
    roles = WorkforceService.list_roles(tenant_id)
    employees = _seed_employees(tenant_id, user_id, departments, roles, fake, rng)
    periods = _seed_periods(tenant_id, user_id)
    report_count, entry_count = _seed_reports_and_entries(
        tenant_id, user_id, periods, employees, rng
    )
    rule_count = _seed_overtime_rules(tenant_id, user_id)
    return {
        "departments": len(departments),
        "employees": len(employees),
        "periods": len(periods),
        "reports": report_count,
        "time_entries": entry_count,
        "overtime_rules": rule_count,
    }


def _seed_departments(tenant_id: int, user_id: int) -> list:
    return [
        WorkforceService.create_department(
            tenant_id, DepartmentEntity(name=name), user_id
        )
        for name in DEPARTMENT_NAMES
    ]


def _seed_employees(
    tenant_id: int,
    user_id: int,
    departments: list,
    roles: list[RoleOut],
    fake: Faker,
    rng: Random,
) -> list[EmployeeOut]:
    employees: list[EmployeeOut] = []
    for _ in range(EMPLOYEE_COUNT):
        dept = rng.choice(departments)
        role = rng.choice(roles)
        hourly_rate = Decimal(f"{rng.uniform(15, 60):.2f}")
        hired_at = date.today() - timedelta(days=rng.randint(30, 1000))
        entity = CreateEmployeeEntity(
            full_name=fake.name(),
            email=fake.unique.email(),
            hired_at=hired_at,
            department_id=dept.id,
            role_id=role.id,
            hourly_rate=hourly_rate,
            contract_hours_per_week=40,
        )
        employees.append(WorkforceService.create_employee(tenant_id, entity, user_id))
    return employees


def _seed_periods(tenant_id: int, user_id: int) -> list:
    today = date.today()
    periods = []
    # 3 past monthly periods + 1 active period covering the last 30 days
    for months_back in range(PAST_PERIODS, 0, -1):
        end = today - timedelta(days=(months_back - 1) * 30 + ACTIVE_PERIOD_DAYS)
        start = end - timedelta(days=ACTIVE_PERIOD_DAYS - 1)
        periods.append(
            TimekeepingService.create_period(
                tenant_id,
                PeriodEntity(
                    name=f"{start.strftime('%b %Y')}",
                    start_date=start,
                    end_date=end,
                ),
                user_id,
            )
        )
    active_start = today - timedelta(days=ACTIVE_PERIOD_DAYS - 1)
    periods.append(
        TimekeepingService.create_period(
            tenant_id,
            PeriodEntity(
                name=f"{active_start.strftime('%b %Y')} (current)",
                start_date=active_start,
                end_date=today,
            ),
            user_id,
        )
    )
    return periods


def _seed_reports_and_entries(
    tenant_id: int,
    user_id: int,
    periods: list,
    employees: list[EmployeeOut],
    rng: Random,
) -> tuple[int, int]:
    """Create reports for past periods and submit/approve a subset.

    Layout (assumes periods sorted oldest → newest, with the last one active):
        - Oldest past period: reports submitted + approved
        - Middle past period: reports submitted (awaiting approval)
        - Newest past period: reports left in draft
        - Active period: no reports yet (users will create their own)
    """
    past_periods = periods[:-1]
    report_count = 0
    entry_count = 0

    for index, period in enumerate(past_periods):
        chosen = rng.sample(employees, k=min(REPORTS_PER_PAST_PERIOD, len(employees)))
        for employee in chosen:
            report = TimekeepingService.create_time_report(
                tenant_id,
                period.id,
                TimeReportEntity(employee_id=employee.id),
                user_id,
            )
            report_count += 1

            n_entries = rng.randint(ENTRIES_PER_REPORT_MIN, ENTRIES_PER_REPORT_MAX)
            period_days = (period.end_date - period.start_date).days + 1
            for _ in range(n_entries):
                entry_date = period.start_date + timedelta(
                    days=rng.randint(0, period_days - 1)
                )
                hours = Decimal(f"{rng.uniform(6.0, 9.0):.2f}")
                TimekeepingService.create_time_entry(
                    tenant_id,
                    report.id,
                    TimeEntryEntity(
                        date=entry_date,
                        hours=hours,
                        description=f"Work on {entry_date.strftime('%A')}",
                    ),
                    user_id,
                )
                entry_count += 1

            if index <= 1:
                TimekeepingService.submit_time_report(tenant_id, report.id, user_id)
            if index == 0:
                TimekeepingService.approve_time_report(tenant_id, report.id, user_id)

    return report_count, entry_count


def _seed_overtime_rules(tenant_id: int, user_id: int) -> int:
    rules_spec = [
        (
            OvertimeRuleEntity(
                name="Weekend hours",
                multiplier=Decimal("2.00"),
                priority=1,
            ),
            [{"condition_type": "day_of_week", "value": "6,7"}],
        ),
        (
            OvertimeRuleEntity(
                name="Over 8h/day",
                multiplier=Decimal("1.50"),
                priority=2,
            ),
            [{"condition_type": "hours_exceeded", "value": "8"}],
        ),
    ]
    for entity, conditions in rules_spec:
        CostingService.create_rule(tenant_id, entity, conditions, user_id)
    return len(rules_spec)
