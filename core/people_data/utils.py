import logging
from itertools import islice

from activity_stream.models import ActivityStreamStaffSSOUser
from core.boto_utils import get_s3_client
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


import os
import sqlalchemy as sa
from django.conf import settings
from smart_open import open as smart_open
from pg_bulk_ingest import ingest, Delete, HighWatermark


def get_data(file):
    logger.info("Loading file from %s", file)
    with smart_open(
        file,
        "r",
        transport_params={
            "client": get_s3_client(),
        },
        encoding="utf-8",
    ) as file_input_stream:  # type: ignore
        for line in file_input_stream:
            yield line


# TODO is this the right place for this function?
def ingest_people_s3():

    table = sa.Table(
        "people_data__jml",
        sa.MetaData(),
        sa.Column("id", sa.VARCHAR, primary_key=True),
        schema="import",  # todo: whats this schema going to be
    )
    logger.info("Ingesting data into table %s", table)
    files = ["s3://jml.local/file.jsonl"]
    for file in files:
        data = get_data(file)

        def batches(_):
            yield None, None, (
                (
                    table,
                    data,
                ),
            )

        engine = sa.create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            ingest(
                conn=conn,
                metadata=table.metadata,
                batches=batches,
                high_watermark=HighWatermark.EARLIEST,
                delete=Delete.OFF,
            )
