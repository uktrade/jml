# Generated by Django 4.1.4 on 2023-01-09 10:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leavers", "0082_alter_leaverinformation_updates"),
    ]

    operations = [
        migrations.AlterField(
            model_name="leavingrequest",
            name="reason_for_leaving",
            field=models.CharField(
                blank=True,
                choices=[
                    ("resignation", "Resignation"),
                    ("retirement", "Retirement"),
                    ("transfer", "Transferring to another Civil Service role"),
                    ("end_of_contract", "End of contract"),
                    ("dismissal", "Dismissal"),
                    ("death_in_service", "Death in service"),
                ],
                max_length=255,
                null=True,
            ),
        ),
    ]
