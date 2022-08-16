from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create Nessus test user"

    def handle(self, *args, **options):
        if hasattr(settings, "NESSUS_TEST_ENABLED") and settings.NESSUS_TEST_ENABLED:
            User = get_user_model()

            user, _ = User.objects.update_or_create(**settings.NESSUS_TEST_USER)
            user.set_password(settings.NESSUS_TEST_USER_PASSWORD)
            user.save()

            self.stdout.write(
                self.style.SUCCESS("Successfully created/updated Nessus test user")
            )

            user.is_superuser = True
            user.is_staff = True
            user.save()

            self.stdout.write(
                self.style.SUCCESS(
                    "Successfully elevated privileges for Nessus test user"
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    "The setting NESSUS_CAN_CREATE_TEST_USER is "
                    "set to false or not found, action not allowed"
                )
            )
