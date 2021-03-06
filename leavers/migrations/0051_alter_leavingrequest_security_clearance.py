# Generated by Django 3.2.14 on 2022-07-21 09:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leavers", "0050_standardise_addresses"),
    ]

    operations = [
        migrations.AlterField(
            model_name="leavingrequest",
            name="security_clearance",
            field=models.CharField(
                blank=True,
                choices=[
                    ("bpss", "Baseline Personnel Security Standard (BPSS)"),
                    ("ctc", "Counter Terrorist Check (CTC)"),
                    ("sc", "Security Check (SC)"),
                    ("esc", "Enhanced Security Check (eSC)"),
                    ("dv", "Developed Vetting (DV)"),
                    ("edv", "Enhanced Developed Vetting (eDV)"),
                ],
                max_length=255,
                null=True,
            ),
        ),
    ]
