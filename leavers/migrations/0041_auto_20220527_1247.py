# Generated by Django 3.2.13 on 2022-05-27 12:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leavers", "0040_alter_leaverinformation_leaver_email"),
    ]

    operations = [
        migrations.AddField(
            model_name="leaverinformation",
            name="contact_address_line1",
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AddField(
            model_name="leaverinformation",
            name="contact_address_line2",
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AddField(
            model_name="leaverinformation",
            name="contact_address_postcode",
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name="leaverinformation",
            name="contact_address_town",
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AddField(
            model_name="leaverinformation",
            name="contact_phone",
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
    ]