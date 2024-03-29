# Generated by Django 4.1.4 on 2023-01-06 15:10

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leavers", "0077_update_flows"),
    ]

    operations = [
        migrations.AddField(
            model_name="leavingrequest",
            name="security_clearance_status",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="security_clearance_status_task_log",
                to="leavers.tasklog",
            ),
        ),
    ]
