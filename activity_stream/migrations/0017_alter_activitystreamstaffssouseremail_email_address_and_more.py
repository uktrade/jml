# Generated by Django 4.0.8 on 2022-11-04 15:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("activity_stream", "0016_auto_20221024_1352"),
    ]

    operations = [
        migrations.AlterField(
            model_name="activitystreamstaffssouseremail",
            name="email_address",
            field=models.EmailField(max_length=255),
        ),
        migrations.AddConstraint(
            model_name="activitystreamstaffssouseremail",
            constraint=models.UniqueConstraint(
                fields=("staff_sso_user", "email_address"),
                name="unique_sso_user_email_address",
            ),
        ),
    ]
