# Generated by Django 4.1.9 on 2023-05-26 14:31

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("leavers", "0093_alter_leavingrequest_reason_for_leaving_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="leavingrequest",
            name="passman_access_removed",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="passman_access_task_log",
                to="leavers.tasklog",
            ),
        ),
    ]