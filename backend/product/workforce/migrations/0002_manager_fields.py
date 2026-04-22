import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("workforce", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="employeemodel",
            name="manager",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="direct_reports",
                to="workforce.employeemodel",
            ),
        ),
        migrations.CreateModel(
            name="DepartmentManagerModel",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("assigned_at", models.DateTimeField(auto_now_add=True)),
                ("left_at", models.DateTimeField(blank=True, null=True)),
                ("left_reason", models.TextField(blank=True, default="")),
                (
                    "department",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="manager_assignments",
                        to="workforce.departmentmodel",
                    ),
                ),
                (
                    "employee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="managed_department_assignments",
                        to="workforce.employeemodel",
                    ),
                ),
            ],
            options={
                "db_table": "workforce_department_managers",
            },
        ),
        migrations.AddIndex(
            model_name="departmentmanagermodel",
            index=models.Index(
                fields=["department", "left_at"],
                name="workforce_d_dept_left_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="departmentmanagermodel",
            index=models.Index(
                fields=["employee"],
                name="workforce_d_manager_emp_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="departmentmanagermodel",
            constraint=models.UniqueConstraint(
                condition=models.Q(("left_at__isnull", True)),
                fields=("department", "employee"),
                name="unique_active_manager_per_department",
            ),
        ),
    ]
