# Generated by Django 4.1.4 on 2022-12-22 10:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leavers", "0081_alter_leavingrequest_options"),
    ]

    operations = [
        migrations.AlterField(
            model_name="leaverinformation",
            name="updates",
            field=models.JSONField(default=dict),
        ),
    ]