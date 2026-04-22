from django.db import models

from infra.authz.models import AuthUserModel
from infra.tenants.models import TenantModel


class DepartmentModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        TenantModel,
        on_delete=models.CASCADE,
        related_name="departments",
    )
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "workforce_departments"
        indexes = [
            models.Index(fields=["tenant", "name"]),
            models.Index(fields=["is_active"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "name"],
                name="unique_department_name_per_tenant",
            )
        ]

    def __str__(self) -> str:
        return self.name


class RoleModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        TenantModel,
        on_delete=models.CASCADE,
        related_name="roles",
    )
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "workforce_roles"
        indexes = [
            models.Index(fields=["tenant", "name"]),
            models.Index(fields=["is_active"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "name"],
                name="unique_role_name_per_tenant",
            )
        ]

    def __str__(self) -> str:
        return self.name


class EmployeeModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        TenantModel,
        on_delete=models.CASCADE,
        related_name="employees",
    )
    user = models.ForeignKey(
        AuthUserModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employee_profiles",
    )
    manager = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="direct_reports",
    )
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    is_active = models.BooleanField(default=True)
    hired_at = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "workforce_employees"
        indexes = [
            models.Index(fields=["tenant", "email"]),
            models.Index(fields=["is_active"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "email"],
                name="unique_employee_email_per_tenant",
            )
        ]

    def __str__(self) -> str:
        return f"{self.full_name} ({self.email})"


class EmployeeDepartmentModel(models.Model):
    """
    Historial de asignaciones de departamento.
    Solo puede haber un registro activo por empleado (left_at IS NULL).
    """

    id = models.BigAutoField(primary_key=True)
    employee = models.ForeignKey(
        EmployeeModel,
        on_delete=models.CASCADE,
        related_name="department_assignments",
    )
    department = models.ForeignKey(
        DepartmentModel,
        on_delete=models.PROTECT,
        related_name="employee_assignments",
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    left_reason = models.TextField(blank=True, default="")

    class Meta:
        db_table = "workforce_employee_departments"
        indexes = [
            models.Index(fields=["employee", "left_at"]),
            models.Index(fields=["department"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["employee"],
                condition=models.Q(left_at__isnull=True),
                name="unique_active_employee_department",
            )
        ]

    def __str__(self) -> str:
        return f"{self.employee_id} -> {self.department_id}"


class EmployeeRoleModel(models.Model):
    """
    Historial de asignaciones de rol.
    Incluye hourly_rate y contract_hours_per_week porque pueden cambiar al cambiar de rol.
    Solo puede haber un registro activo por empleado (left_at IS NULL).
    """

    id = models.BigAutoField(primary_key=True)
    employee = models.ForeignKey(
        EmployeeModel,
        on_delete=models.CASCADE,
        related_name="role_assignments",
    )
    role = models.ForeignKey(
        RoleModel,
        on_delete=models.PROTECT,
        related_name="employee_assignments",
    )
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2)
    contract_hours_per_week = models.PositiveSmallIntegerField()
    assigned_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    left_reason = models.TextField(blank=True, default="")

    class Meta:
        db_table = "workforce_employee_roles"
        indexes = [
            models.Index(fields=["employee", "left_at"]),
            models.Index(fields=["role"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["employee"],
                condition=models.Q(left_at__isnull=True),
                name="unique_active_employee_role",
            )
        ]

    def __str__(self) -> str:
        return f"{self.employee_id} -> {self.role_id}"


class DepartmentManagerModel(models.Model):
    """
    Active and historical manager assignments for a department.
    A department can have multiple active managers simultaneously.
    """

    id = models.BigAutoField(primary_key=True)
    department = models.ForeignKey(
        DepartmentModel,
        on_delete=models.CASCADE,
        related_name="manager_assignments",
    )
    employee = models.ForeignKey(
        EmployeeModel,
        on_delete=models.PROTECT,
        related_name="managed_department_assignments",
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    left_reason = models.TextField(blank=True, default="")

    class Meta:
        db_table = "workforce_department_managers"
        indexes = [
            models.Index(fields=["department", "left_at"]),
            models.Index(fields=["employee"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["department", "employee"],
                condition=models.Q(left_at__isnull=True),
                name="unique_active_manager_per_department",
            )
        ]

    def __str__(self) -> str:
        return f"{self.employee_id} -> dept {self.department_id}"
