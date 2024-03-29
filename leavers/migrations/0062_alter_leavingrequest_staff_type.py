# Generated by Django 3.2.15 on 2022-09-26 09:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leavers", "0061_tasklog_value"),
    ]

    operations = [
        migrations.AlterField(
            model_name="leavingrequest",
            name="staff_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("civil_servant", "Civil servant"),
                    ("fast_streamers", "Fast streamers"),
                    ("contractor", "Contractor"),
                    ("bench_contractor", "Bench contractor"),
                ],
                max_length=255,
                null=True,
            ),
        ),
    ]
