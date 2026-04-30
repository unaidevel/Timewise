from datetime import date
from decimal import Decimal

import pytest

from infra.common.exceptions import UnprocessableEntity
from product.workforce.entities.workforce_entities import (
    DepartmentEntity,
    EmployeeEntity,
    EmployeeRoleEntity,
    EmployeeUpdateEntity,
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

    def test_accepts_min_contract_hours(self):
        entity = EmployeeRoleEntity(
            hourly_rate=Decimal("25.00"), contract_hours_per_week=1
        )
        assert entity.contract_hours_per_week == 1

    def test_raises_on_negative_contract_hours(self):
        with pytest.raises(UnprocessableEntity, match="between 1 and 168"):
            EmployeeRoleEntity(hourly_rate=Decimal("25.00"), contract_hours_per_week=-1)


class TestDepartmentEntityBoundaries:
    def test_accepts_name_at_200_chars(self):
        entity = DepartmentEntity(name="x" * 200)
        assert len(entity.name) == 200


class TestRoleEntityBoundaries:
    def test_accepts_name_at_200_chars(self):
        entity = RoleEntity(name="r" * 200)
        assert len(entity.name) == 200


class TestEmployeeEntityBoundaries:
    def test_accepts_full_name_at_200_chars(self):
        entity = EmployeeEntity(
            full_name="x" * 200,
            email="user@example.com",
            hired_at=date(2024, 1, 1),
        )
        assert len(entity.full_name) == 200

    def test_raises_on_full_name_over_200_chars(self):
        with pytest.raises(UnprocessableEntity, match="200 characters"):
            EmployeeEntity(
                full_name="x" * 201,
                email="user@example.com",
                hired_at=date(2024, 1, 1),
            )

    def test_preserves_hired_at_value(self):
        entity = EmployeeEntity(
            full_name="Jane Doe",
            email="jane@example.com",
            hired_at=date(2024, 6, 15),
        )
        assert entity.hired_at == date(2024, 6, 15)

    def test_rejects_email_without_dot(self):
        with pytest.raises(UnprocessableEntity, match="Invalid email"):
            EmployeeEntity(
                full_name="Jane",
                email="user@example",
                hired_at=date(2024, 1, 1),
            )

    def test_rejects_email_without_at(self):
        with pytest.raises(UnprocessableEntity, match="Invalid email"):
            EmployeeEntity(
                full_name="Jane",
                email="user.example.com",
                hired_at=date(2024, 1, 1),
            )


class TestEmployeeUpdateEntity:
    def test_accepts_all_none_values(self):
        entity = EmployeeUpdateEntity(full_name=None, email=None, hired_at=None)

        assert entity.full_name is None
        assert entity.email is None
        assert entity.hired_at is None

    def test_validates_full_name_when_provided(self):
        entity = EmployeeUpdateEntity(full_name="  Jane  ", email=None, hired_at=None)

        assert entity.full_name == "Jane"

    def test_rejects_blank_full_name_when_provided(self):
        with pytest.raises(UnprocessableEntity, match="cannot be blank"):
            EmployeeUpdateEntity(full_name="   ", email=None, hired_at=None)

    def test_rejects_too_long_full_name_when_provided(self):
        with pytest.raises(UnprocessableEntity, match="200 characters"):
            EmployeeUpdateEntity(full_name="x" * 201, email=None, hired_at=None)

    def test_validates_email_when_provided(self):
        entity = EmployeeUpdateEntity(
            full_name=None, email="USER@Example.COM", hired_at=None
        )

        assert entity.email == "user@example.com"

    def test_rejects_invalid_email_when_provided(self):
        with pytest.raises(UnprocessableEntity, match="Invalid email"):
            EmployeeUpdateEntity(full_name=None, email="not-an-email", hired_at=None)

    def test_preserves_hired_at_when_provided(self):
        d = date(2024, 6, 15)
        entity = EmployeeUpdateEntity(full_name=None, email=None, hired_at=d)

        assert entity.hired_at == d
