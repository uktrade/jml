import json
import logging
from itertools import islice

import sqlalchemy as sa
from django.conf import settings
from pg_bulk_ingest import Delete, HighWatermark, ingest

from activity_stream.models import ActivityStreamStaffSSOUser
from core.boto_utils import PeopleDataS3Ingest
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

            sso_user.uksbs_person_id = ""
            sso_user.employee_numbers = []

            chunk_count += 1

            people_data_hits_with_person_id = [
                hit for hit in people_data_hits if hit["uksbs_person_id"]
            ]

            if not people_data_hits_with_person_id:
                continue

            if len(people_data_hits_with_person_id) > 1:
                logger.exception(
                    Exception(
                        "Multiple people data records found (with person IDs) "
                        f"for {sso_user}"
                    )
                )
                continue

            people_data = people_data_hits_with_person_id[0]

            sso_user.uksbs_person_id = people_data["uksbs_person_id"]
            sso_user.employee_numbers = people_data["employee_numbers"]

        ActivityStreamStaffSSOUser.objects.bulk_update(
            sso_users, ["uksbs_person_id", "employee_numbers"]
        )

        logger.info(f"{chunk_count}/{CHUNK_SIZE} records updated this chunk")

        total_count += chunk_count

    logger.info(f"Total number of updated records {total_count}")


def ingest_people_data_from_s3_to_table() -> None:
    table = sa.Table(
        "people_data__jml",
        sa.MetaData(),
        sa.Column("email_address", sa.String),
        sa.Column("person_id", sa.String(255)),
        sa.Column("employee_numbers", sa.ARRAY(sa.String)),
        sa.Column("person_type", sa.String),
        sa.Column("grade", sa.String),
        sa.Column("grade_Level", sa.String),
        schema="import",
    )

    ingest_manager = PeopleDataS3Ingest()
    data = ingest_manager.get_data_to_ingest()

    ingest_data: list[tuple] = []
    for row in data:
        item = json.loads(row)
        ingest_row = (
            item["email_address"],
            item["person_id"],
            item["employee_numbers"],
            item["person_type"],
            item["grade"],
            item["grade_Level"],
        )
        ingest_data.append(ingest_row)

    logger.info("Ingesting data into table %s", table)

    def batches(_):
        yield (None, None, ((table, row) for row in ingest_data))

    # sqlalchemy doesn't understand `psql://`
    db_url = settings.DATABASE_URL.replace("psql://", "postgresql://")
    engine = sa.create_engine(db_url)
    with engine.connect() as conn:
        ingest(
            conn=conn,
            metadata=table.metadata,
            batches=batches,
            high_watermark=HighWatermark.EARLIEST,
            delete=Delete.BEFORE_FIRST_BATCH,
        )

    # ingest_manager.cleanup()
