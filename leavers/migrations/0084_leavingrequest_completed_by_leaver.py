# Generated by Django 4.1.4 on 2023-01-13 11:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leavers", "0083_alter_leavingrequest_reason_for_leaving"),
    ]

    operations = [
        migrations.AddField(
            model_name="leavingrequest",
            name="completed_by_leaver",
            field=models.BooleanField(default=True),
        ),
    ]
