# Generated by Django 3.2.9 on 2022-01-20 12:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leavers", "0010_leavingrequest_data_recipient_activitystream_user"),
    ]

    operations = [
        migrations.AddField(
            model_name="leavingrequest",
            name="uksbs_pdf_data",
            field=models.JSONField(blank=True, null=True),
        ),
    ]