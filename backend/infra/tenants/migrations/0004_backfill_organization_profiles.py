from django.db import migrations


def backfill_profiles(apps, schema_editor):
    TenantModel = apps.get_model("tenants", "TenantModel")
    OrganizationProfileModel = apps.get_model("tenants", "OrganizationProfileModel")
    existing = set(OrganizationProfileModel.objects.values_list("tenant_id", flat=True))
    profiles = [
        OrganizationProfileModel(tenant_id=tenant_id)
        for tenant_id in TenantModel.objects.values_list("id", flat=True)
        if tenant_id not in existing
    ]
    if profiles:
        OrganizationProfileModel.objects.bulk_create(profiles)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("tenants", "0003_organizationprofilemodel"),
    ]

    operations = [
        migrations.RunPython(backfill_profiles, reverse_code=noop),
    ]
