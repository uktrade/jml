# Generated by Django 3.2.11 on 2022-02-16 10:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leavers", "0018_leavingrequest_sre_complete"),
    ]

    operations = [
        migrations.AddField(
            model_name="leavingrequest",
            name="task_logs",
            field=models.ManyToManyField(to="leavers.TaskLog"),
        ),
    ]