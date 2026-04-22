import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("workforce", "0002_manager_fields"),
        ("authz", "0002_authloginattemptmodel_and_more"),
    ]

    operations = [
        # DepartmentModel
        migrations.AddField(
            model_name="departmentmodel",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_departments",
                to="authz.authusermodel",
            ),
        ),
        migrations.AddField(
            model_name="departmentmodel",
            name="updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="updated_departments",
                to="authz.authusermodel",
            ),
        ),
        # RoleModel
        migrations.AddField(
            model_name="rolemodel",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_roles",
                to="authz.authusermodel",
            ),
        ),
        migrations.AddField(
            model_name="rolemodel",
            name="updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="updated_roles",
                to="authz.authusermodel",
            ),
        ),
        # EmployeeModel
        migrations.AddField(
            model_name="employeemodel",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_employees",
                to="authz.authusermodel",
            ),
        ),
        migrations.AddField(
            model_name="employeemodel",
            name="updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="updated_employees",
                to="authz.authusermodel",
            ),
        ),
        # EmployeeDepartmentModel
        migrations.AddField(
            model_name="employeedepartmentmodel",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_employee_departments",
                to="authz.authusermodel",
            ),
        ),
        migrations.AddField(
            model_name="employeedepartmentmodel",
            name="updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="updated_employee_departments",
                to="authz.authusermodel",
            ),
        ),
        # EmployeeRoleModel
        migrations.AddField(
            model_name="employeerolemodel",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_employee_roles",
                to="authz.authusermodel",
            ),
        ),
        migrations.AddField(
            model_name="employeerolemodel",
            name="updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="updated_employee_roles",
                to="authz.authusermodel",
            ),
        ),
        # DepartmentManagerModel
        migrations.AddField(
            model_name="departmentmanagermodel",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_department_managers",
                to="authz.authusermodel",
            ),
        ),
        migrations.AddField(
            model_name="departmentmanagermodel",
            name="updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="updated_department_managers",
                to="authz.authusermodel",
            ),
        ),
    ]
