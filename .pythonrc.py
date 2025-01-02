from typing import Any

from django.db import connections

from activity_stream.models import ActivityStreamStaffSSOUser
from core.people_data.interfaces import row_to_dict


def get_sso_user_by_email(email: str) -> ActivityStreamStaffSSOUser:
    return ActivityStreamStaffSSOUser.objects.get(sso_emails__email_address=email)


def query_people_data_by_email(email: str) -> list[dict[str, Any]]:
    with connections["default"].cursor() as cursor:
        cursor.execute(
            ("SELECT * FROM data_import__people_data__jml" " WHERE email_address = %s"),
            [email],
        )
        rows = cursor.fetchall()

        return [row_to_dict(cursor=cursor, row=row) for row in rows]
