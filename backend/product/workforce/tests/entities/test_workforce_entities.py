from datetime import date
from decimal import Decimal

import pytest

from infra.common.http_exceptions import UnprocessableEntity
from product.workforce.entities.workforce_entities import (
    DepartmentEntity,
    EmployeeEntity,
    EmployeeRoleEntity,
    RoleEntity,
)


class TestDepartmentEntity:
    def test_strips_whitespace_from_name(self):
        entity = DepartmentEntity(name="  Engineering  ")
        assert entity.name == "Engineering"

    def test_raises_on_blank_name(self):
        with pytest.raises(UnprocessableEntity, match="cannot be blank"):
            DepartmentEntity(name="   ")

    def test_raises_on_name_exceeding_200_chars(self):
        with pytest.raises(UnprocessableEntity, match="200 characters"):
            DepartmentEntity(name="x" * 201)

    def test_accepts_single_char_name(self):
        entity = DepartmentEntity(name="A")
        assert entity.name == "A"


class TestRoleEntity:
    def test_strips_whitespace_from_name(self):
        entity = RoleEntity(name="  Senior Engineer  ")
        assert entity.name == "Senior Engineer"

    def test_raises_on_blank_name(self):
        with pytest.raises(UnprocessableEntity, match="cannot be blank"):
            RoleEntity(name="   ")

    def test_raises_on_name_exceeding_200_chars(self):
        with pytest.raises(UnprocessableEntity, match="200 characters"):
            RoleEntity(name="r" * 201)


class TestEmployeeEntity:
    def test_normalizes_email_to_lowercase(self):
        entity = EmployeeEntity(
            full_name="Jane Doe",
            email="  JANE@Example.COM  ",
            hired_at=date(2024, 1, 15),
        )
        assert entity.email == "jane@example.com"

    def test_strips_whitespace_from_full_name(self):
        entity = EmployeeEntity(
            full_name="  Jane Doe  ",
            email="jane@example.com",
            hired_at=date(2024, 1, 15),
        )
        assert entity.full_name == "Jane Doe"

    def test_raises_on_blank_full_name(self):
        with pytest.raises(UnprocessableEntity, match="cannot be blank"):
            EmployeeEntity(
                full_name="   ", email="jane@example.com", hired_at=date(2024, 1, 15)
            )

    def test_raises_on_invalid_email(self):
        with pytest.raises(UnprocessableEntity, match="Invalid email"):
            EmployeeEntity(
                full_name="Jane", email="not-an-email", hired_at=date(2024, 1, 15)
            )


class TestEmployeeRoleEntity:
    def test_raises_on_zero_hourly_rate(self):
        with pytest.raises(UnprocessableEntity, match="greater than zero"):
            EmployeeRoleEntity(hourly_rate=Decimal("0"), contract_hours_per_week=40)

    def test_raises_on_negative_hourly_rate(self):
        with pytest.raises(UnprocessableEntity, match="greater than zero"):
            EmployeeRoleEntity(hourly_rate=Decimal("-5.00"), contract_hours_per_week=40)

    def test_raises_on_zero_contract_hours(self):
        with pytest.raises(UnprocessableEntity, match="between 1 and 168"):
            EmployeeRoleEntity(hourly_rate=Decimal("25.00"), contract_hours_per_week=0)

    def test_raises_on_contract_hours_exceeding_168(self):
        with pytest.raises(UnprocessableEntity, match="between 1 and 168"):
            EmployeeRoleEntity(
                hourly_rate=Decimal("25.00"), contract_hours_per_week=169
            )

    def test_accepts_max_contract_hours(self):
        entity = EmployeeRoleEntity(
            hourly_rate=Decimal("25.00"), contract_hours_per_week=168
        )
        assert entity.contract_hours_per_week == 168
