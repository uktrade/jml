from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create Nessus test user"

    def add_arguments(self, parser):
        parser.add_argument(
            "--elevate",
            help="Should the test users privileges be elevated?",
            dest="elevate",
        )

    def handle(self, *args, **options):
        if hasattr(settings, "NESSUS_TEST_ENABLED") and settings.NESSUS_TEST_ENABLED:
            elevate = options["elevate"]

            User = get_user_model()

            user, _ = User.objects.update_or_create(**settings.NESSUS_TEST_USER)
            user.set_password(settings.NESSUS_TEST_USER_PASSWORD)
            user.save()

            self.stdout.write(
                self.style.SUCCESS("Successfully created/updated Nessus test user")
            )

            if elevate:
                user.is_superuser = True
                user.is_staff = True
                user.save()

                self.stdout.write(
                    self.style.SUCCESS(
                        "Successfully elevated privileges for Nessus user"
                    )
                )
        else:
            self.stdout.write(
                self.style.ERROR(
                    "The setting NESSUS_CAN_CREATE_TEST_USER is "
                    "set to false or not found, action not allowed"
                )
            )
