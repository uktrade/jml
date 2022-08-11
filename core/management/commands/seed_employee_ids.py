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

        with connections["people_data"].cursor() as cursor:
            for user in users:
                cursor.execute(
                    "INSERT INTO dit.people_data__identities "
                    "(sso_user_id, employee_numbers) VALUES(%s, %s)",
                    (user.sso_legacy_user_id, [employee_id_1, employee_id_2]),
                )
                employee_id_1 += 1
                employee_id_2 += 1
            connections["people_data"].commit()

        self.stdout.write(
            self.style.SUCCESS(f"Added employee id records to {len(users)} users")
        )
