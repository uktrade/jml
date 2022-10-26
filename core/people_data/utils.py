import logging
from itertools import islice

from activity_stream.models import ActivityStreamStaffSSOUser
from core.people_data import get_people_data_interface

logger = logging.getLogger(__name__)

CHUNK_SIZE = 100


def ingest_people_data():
    people_data_interface = get_people_data_interface()
    people_data_iterator = people_data_interface.get_all()

    total_count = 0

    while chunk := list(islice(people_data_iterator, CHUNK_SIZE)):
        sso_user_emails = [email for row in chunk if (email := row["email_address"])]

        if not sso_user_emails:
            continue

        sso_users = ActivityStreamStaffSSOUser.objects.with_emails().filter(
            emails__overlap=sso_user_emails
        )

        people_data_lookup = {row["email_address"]: row for row in chunk}

        chunk_count = 0

        for sso_user in sso_users:
            people_data_hits = [
                hit
                for email in sso_user.emails
                if (hit := people_data_lookup.get(email))
            ]

            if not people_data_hits:
                continue

            if len(people_data_hits) > 1:
                # TODO: We need to log this somewhere. A big assumption of the data has
                # been broken.
                continue

            people_data = people_data_hits[0]

            sso_user.uksbs_person_id = people_data["uksbs_person_id"] or ""
            sso_user.employee_numbers = people_data["employee_numbers"] or []

            chunk_count += 1

        ActivityStreamStaffSSOUser.objects.bulk_update(
            sso_users, ["uksbs_person_id", "employee_numbers"]
        )

        logger.info(f"{chunk_count}/{CHUNK_SIZE} records updated this chunk")

        total_count += chunk_count

    logger.info(f"Total number of updated records {total_count}")
