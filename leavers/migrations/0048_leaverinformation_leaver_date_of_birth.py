# Generated by Django 3.2.14 on 2022-07-15 13:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leavers", "0047_alter_leavingrequest_security_clearance"),
    ]

    operations = [
        migrations.AddField(
            model_name="leaverinformation",
            name="leaver_date_of_birth",
            field=models.DateField(blank=True, null=True),
        ),
    ]
