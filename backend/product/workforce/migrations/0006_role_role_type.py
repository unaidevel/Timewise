from django.db import migrations, models

NAME_TO_TYPE = {
    "Manager": "manager",
    "Employee": "employee",
    "Intern": "intern",
    "Freelance": "freelance",
}


def backfill_role_type(apps, schema_editor):
    Role = apps.get_model("workforce", "RoleModel")
    for name, role_type in NAME_TO_TYPE.items():
        Role.objects.filter(name=name).update(role_type=role_type)


def noop_reverse(apps, schema_editor):
    return


class Migration(migrations.Migration):
    dependencies = [
        (
            "workforce",
            "0005_rename_workforce_d_departm_140051_idx_workforce_d_departm_cd93ad_idx_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="rolemodel",
            name="role_type",
            field=models.CharField(
                choices=[
                    ("manager", "Manager"),
                    ("employee", "Employee"),
                    ("intern", "Intern"),
                    ("freelance", "Freelance"),
                    ("custom", "Custom"),
                ],
                default="custom",
                max_length=20,
            ),
        ),
        migrations.RunPython(backfill_role_type, noop_reverse),
    ]
