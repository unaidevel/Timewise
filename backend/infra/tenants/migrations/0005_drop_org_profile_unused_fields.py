from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("tenants", "0004_backfill_organization_profiles"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="organizationprofilemodel",
            name="workspace_name",
        ),
        migrations.RemoveField(
            model_name="organizationprofilemodel",
            name="fiscal_year_start",
        ),
        migrations.RemoveField(
            model_name="organizationprofilemodel",
            name="default_locale",
        ),
    ]
