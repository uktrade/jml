# Generated by Django 3.2.9 on 2022-01-21 13:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leavers", "0011_leavingrequest_uksbs_pdf_data"),
    ]

    operations = [
        migrations.AddField(
            model_name="leavingrequest",
            name="holds_government_procurement_card",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="leavingrequest",
            name="is_rosa_user",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="leavingrequest",
            name="security_clearance",
            field=models.CharField(
                blank=True,
                choices=[("security_clearance_1", "Security clearance 1")],
                max_length=255,
                null=True,
            ),
        ),
    ]