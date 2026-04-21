from django.contrib import admin

from .models import (
    DepartmentModel,
    EmployeeDepartmentModel,
    EmployeeModel,
    EmployeeRoleModel,
    RoleModel,
)


@admin.register(DepartmentModel)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "is_active", "created_at")
    search_fields = ("name", "tenant__slug")
    list_filter = ("is_active",)


@admin.register(RoleModel)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "is_active", "created_at")
    search_fields = ("name", "tenant__slug")
    list_filter = ("is_active",)


@admin.register(EmployeeModel)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "tenant", "is_active", "hired_at")
    search_fields = ("full_name", "email", "tenant__slug")
    list_filter = ("is_active",)


@admin.register(EmployeeDepartmentModel)
class EmployeeDepartmentAdmin(admin.ModelAdmin):
    list_display = ("employee", "department", "assigned_at", "left_at")
    search_fields = ("employee__full_name", "department__name")
    list_filter = ("left_at",)


@admin.register(EmployeeRoleModel)
class EmployeeRoleAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "role",
        "hourly_rate",
        "contract_hours_per_week",
        "assigned_at",
        "left_at",
    )
    search_fields = ("employee__full_name", "role__name")
    list_filter = ("left_at",)
