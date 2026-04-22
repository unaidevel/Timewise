from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("timekeeping", "0002_rename_timekeeping_period_tenant_status_idx_timekeeping_tenant__4b3396_idx_and_more"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="timeentrymodel",
            constraint=models.CheckConstraint(
                condition=models.Q(hours__gte=Decimal("0.01"), hours__lte=Decimal("24")),
                name="timekeeping_entry_hours_range",
            ),
        ),
    ]
