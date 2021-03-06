# Generated by Django 3.2.13 on 2022-07-07 11:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0003_add_user_user_id"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="user",
            name="unique_legacy_sso_user_id",
        ),
        migrations.RenameField(
            model_name="user",
            old_name="legacy_sso_user_id",
            new_name="sso_legacy_user_id",
        ),
        migrations.AddField(
            model_name="user",
            name="sso_email_user_id",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                fields=("sso_legacy_user_id",), name="unique_sso_legacy_user_id"
            ),
        ),
    ]
