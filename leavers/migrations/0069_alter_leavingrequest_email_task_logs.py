# Generated by Django 4.0.8 on 2022-10-25 10:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leavers", "0068_remove_leavingrequest_sso_access_removed"),
    ]

    operations = [
        migrations.AlterField(
            model_name="leavingrequest",
            name="email_task_logs",
            field=models.ManyToManyField(related_name="+", to="leavers.tasklog"),
        ),
    ]