# Generated by Django 3.2.11 on 2022-02-21 16:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leavers", "0019_leavingrequest_task_logs"),
    ]

    operations = [
        migrations.AddField(
            model_name="leavingrequest",
            name="line_manager_complete",
            field=models.BooleanField(default=False),
        ),
    ]
