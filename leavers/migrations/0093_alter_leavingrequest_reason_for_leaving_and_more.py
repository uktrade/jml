# Generated by Django 4.1.6 on 2023-02-16 15:27

from django.db import migrations, models


def update_leaving_requests(apps, schema_editor):
    """
    Update LeavingRequest with choice changes.
    """
    LeavingRequest = apps.get_model("leavers", "LeavingRequest")

    # Get leaving requests with staff types to update.
    lrs_with_staff_types_to_update = LeavingRequest.objects.filter(
        staff_type__in=[
            "fast_streamers",
            "loan",
        ],
    )
    # Update to "other".
    lrs_with_staff_types_to_update.update(staff_type="other")


class Migration(migrations.Migration):
    dependencies = [
        ("leavers", "0092_alter_leavingrequest_staff_type"),
    ]

    operations = [
        migrations.RunPython(update_leaving_requests, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="leavingrequest",
            name="reason_for_leaving",
            field=models.CharField(
                blank=True,
                choices=[
                    ("transfer", "Transferring to another Civil Service role"),
                    ("end_of_contract", "End of contract"),
                    ("resignation", "Resignation"),
                    ("retirement", "Retirement"),
                    ("ill_health_retirement", "Retirement due to ill health"),
                    ("dismissal", "Dismissal"),
                    ("death_in_service", "Death in service"),
                ],
                max_length=255,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="leavingrequest",
            name="staff_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("civil_servant", "Civil servant"),
                    ("contractor", "Contractor (for example, Hays)"),
                    ("bench_contractor", "Bench contractor (for example, Profusion)"),
                    ("other", "Other"),
                ],
                max_length=255,
                null=True,
            ),
        ),
    ]
