# Generated by Django 4.1.6 on 2023-02-09 13:55

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("leavers", "0090_update_flows"),
    ]

    operations = [
        migrations.AddField(
            model_name="leavingrequest",
            name="docker_user_access_removed",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="docker_user_task_log",
                to="leavers.tasklog",
            ),
        ),
    ]
