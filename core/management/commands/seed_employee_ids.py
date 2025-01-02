from django.core.management.base import BaseCommand
from django.db import connections
from django.db.models.query import QuerySet

from user.models import User


class Command(BaseCommand):
    help = "Seed employee ids"

    def handle(self, *args, **options):
        users: QuerySet[User] = User.objects.filter(sso_legacy_user_id__isnull=False)

        employee_id_1 = 10000000
        employee_id_2 = 100000
        person_id = 10000

        with connections["default"].cursor() as cursor:
            for user in users:
                cursor.execute(
                    """
                    INSERT INTO public.data_import__people_data__jml (
                        email_address,
                        person_id,
                        employee_numbers
                    )
                    VALUES(%s, %s, %s)
                    """,
                    (
                        user.email,
                        person_id,
                        [employee_id_1, employee_id_2],
                    ),
                )
                employee_id_1 += 1
                employee_id_2 += 1
                person_id += 1
            connections["default"].commit()

        self.stdout.write(
            self.style.SUCCESS(f"Added employee id records to {len(users)} users")
        )
