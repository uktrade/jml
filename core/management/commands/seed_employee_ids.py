from django.core.management.base import BaseCommand
from django.db import connections
from django.db.models.query import QuerySet
from django.db.utils import ProgrammingError

from core.people_data.utils import ingest_people_data_from_s3_to_table
from user.models import User


class Command(BaseCommand):
    help = "Seed employee ids (DO NOT USE IN PROD)"

    def handle(self, *args, **options):
        ingest_people_data_from_s3_to_table()

        users: QuerySet[User] = User.objects.filter(sso_legacy_user_id__isnull=False)

        employee_id_1 = 20000000
        employee_id_2 = 200000
        person_id = 20000

        with connections["default"].cursor() as cursor:
            for user in users:
                try:
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
                except ProgrammingError:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Failed to add employee id records to {user.email}"
                        )
                    )
                    continue

                employee_id_1 += 1
                employee_id_2 += 1
                person_id += 1
            connections["default"].commit()

        self.stdout.write(
            self.style.SUCCESS(f"Added employee id records to {len(users)} users")
        )
