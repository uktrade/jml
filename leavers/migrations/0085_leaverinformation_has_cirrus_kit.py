# Generated by Django 4.1.4 on 2023-01-16 18:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leavers", "0084_leavingrequest_completed_by_leaver"),
    ]

    operations = [
        migrations.AddField(
            model_name="leaverinformation",
            name="has_cirrus_kit",
            field=models.BooleanField(blank=True, null=True),
        ),
    ]