from django.contrib import admin
from unfold.admin import ModelAdmin

from product.workforce.models import (
    DepartmentModel,
    EmployeeDepartmentModel,
    EmployeeModel,
    EmployeeRoleModel,
    RoleModel,
)


@admin.register(DepartmentModel)
class DepartmentAdmin(ModelAdmin):
    list_display = ("id", "name", "tenant", "is_active", "created_at")
    search_fields = ("name", "tenant__slug")
    list_filter = ("is_active", "tenant")
    list_select_related = ("tenant",)


@admin.register(RoleModel)
class RoleAdmin(ModelAdmin):
    list_display = ("id", "name", "tenant", "is_active", "created_at")
    search_fields = ("name", "tenant__slug")
    list_filter = ("is_active", "tenant")
    list_select_related = ("tenant",)


@admin.register(EmployeeModel)
class EmployeeAdmin(ModelAdmin):
    list_display = ("id", "full_name", "email", "tenant", "is_active", "hired_at")
    search_fields = ("full_name", "email", "tenant__slug")
    list_filter = ("is_active", "tenant")
    list_select_related = ("tenant",)


@admin.register(EmployeeDepartmentModel)
class EmployeeDepartmentAdmin(ModelAdmin):
    list_display = ("id", "employee", "department", "tenant", "assigned_at", "left_at")
    search_fields = (
        "employee__full_name",
        "department__name",
        "employee__tenant__slug",
    )
    list_filter = ("left_at", "employee__tenant")
    list_select_related = ("employee__tenant", "department")

    @admin.display(description="Tenant", ordering="employee__tenant__slug")
    def tenant(self, obj):
        return obj.employee.tenant


@admin.register(EmployeeRoleModel)
class EmployeeRoleAdmin(ModelAdmin):
    list_display = (
        "id",
        "employee",
        "role",
        "tenant",
        "hourly_rate",
        "contract_hours_per_week",
        "assigned_at",
        "left_at",
    )
    search_fields = ("employee__full_name", "role__name", "employee__tenant__slug")
    list_filter = ("left_at", "employee__tenant")
    list_select_related = ("employee__tenant", "role")

    @admin.display(description="Tenant", ordering="employee__tenant__slug")
    def tenant(self, obj):
        return obj.employee.tenant
