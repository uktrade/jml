from itertools import islice

from activity_stream.models import ActivityStreamStaffSSOUser
from core.people_data import get_people_data_interface


def ingest_people_data():
    people_data_interface = get_people_data_interface()

    people_data_iterator = people_data_interface.get_all()

    while chunk := list(islice(people_data_iterator, 100)):
        sso_user_emails = [row["email_address"] for row in chunk]

        sso_users = ActivityStreamStaffSSOUser.objects.with_emails().filter(
            emails__overlap=sso_user_emails
        )

        people_data_lookup = {row["email_address"]: row for row in chunk}

        for sso_user in sso_users:
            people_data_hits = [people_data_lookup[email] for email in sso_user.emails]

            if len(people_data_hits) > 1:
                # TODO: We need to log this somewhere. A big assumption of the data has
                # been broken.
                continue

            people_data = people_data_hits[0]

            sso_user.uksbs_person_id = people_data["uksbs_person_id"]
            sso_user.employee_numbers = people_data["employee_numbers"] or []

        ActivityStreamStaffSSOUser.objects.bulk_update(
            sso_users, ["uksbs_person_id", "employee_numbers"]
        )
