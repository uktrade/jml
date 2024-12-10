import json

import logging
from typing import List

from django.conf import settings

import smart_open

from activity_stream import models, staff_sso
from core.boto_utils import get_s3_resource

logger = logging.getLogger(__name__)


def _do_get_staff_sso_s3_object_summaries(s3_bucket):
    logger.info("ingest_staff_sso_s3: Reading files from bucket %s", s3_bucket)
    files = (
        s3_bucket.objects.filter()
    )  # TODO do we need to use a prefix filter? If not change the .filter() to .all()
    # Get the list of files, oldest first. Process in that order, so any changes in newer files
    # take precedence
    sorted_files = sorted(files, key=lambda x: x.last_modified, reverse=False)
    for file in sorted_files:
        file.source_key = f"s3://{file.bucket_name}/{file.key}"
        logger.info("ingest_staff_sso_s3: Found S3 file with key %s", file.source_key)
    return sorted_files


def _process_staff_sso_file(client, source_key) -> list[int]:
    created_updated_ids = []

    with smart_open(
        source_key,
        "r",
        transport_params={
            "client": client,
        },
        encoding="utf-8",
    ) as file_input_stream:
        logger.info("ingest_staff_sso_s3: Processing file %s", source_key)
        for line in file_input_stream:
            user = json.loads(line)
            user_obj = user["object"]
            (
                as_staff_sso_user,
                _,
            ) = models.ActivityStreamStaffSSOUser.objects.update_or_create(
                identifier=user_obj["id"],
                defaults={
                    "available": True,
                    "name": user_obj["name"],
                    "obj_type": user_obj["type"],
                    "first_name": user_obj["dit:firstName"],  # /PS-IGNORE
                    "last_name": user_obj["dit:lastName"],  # /PS-IGNORE
                    "user_id": user_obj["dit:StaffSSO:User:userId"],
                    "status": user_obj["dit:StaffSSO:User:status"],
                    "last_accessed": user_obj["dit:StaffSSO:User:lastAccessed"],
                    "joined": user_obj["dit:StaffSSO:User:joined"],
                    "email_user_id": user_obj["dit:StaffSSO:User:emailUserId"],
                    "contact_email_address": user_obj[
                        "dit:StaffSSO:User:contactEmailAddress"
                    ],
                    "became_inactive_on": user_obj[
                        "dit:StaffSSO:User:becameInactiveOn"
                    ],
                },
            )

            for email in user_obj["dit:emailAddress"]:
                models.ActivityStreamStaffSSOUserEmail.objects.get_or_create(
                    email_address=email,
                    staff_sso_user=as_staff_sso_user,
                )

            created_updated_ids.append(as_staff_sso_user.id)
            logger.info(
                "ingest_staff_sso_s3: Added SSO activity stream record for %s",
                as_staff_sso_user.id,
            )

    return created_updated_ids


def _get_created_updated_ids(files, client) -> list[int]:
    created_updated_ids = list[int]()
    for file in files:
        created_updated_ids.extend(_process_staff_sso_file(client, file.source_key))

    return list(set(created_updated_ids))


def ingest_staff_sso_s3() -> None:
    logger.info("ingest_staff_sso_s3: Starting S3 ingest")

    s3_resource = get_s3_resource()
    bucket = s3_resource.Bucket(settings.DATA_FLOW_UPLOADS_BUCKET)

    logger.info("ingest_staff_sso_s3: Reading files from bucket %s", bucket)

    files = _do_get_staff_sso_s3_object_summaries(bucket)
    if len(files) == 0:
        logger.info(
            "ingest_staff_sso_s3: No files in bucket %s, stopping task execution",
            bucket,
        )
        return

    created_updated_ids: List[int] = _get_created_updated_ids(
        files, s3_resource.meta.client
    )

    delete_keys = [{"Key": file.key} for file in files]
    logger.info("ingest_staff_sso_s3: Deleting keys %s", delete_keys)
    bucket.delete_objects(Delete={"Objects": delete_keys})

    # Mark the Staff SSO objects that are no longer in the S3 file.
    if settings.APP_ENV == "production":
        logger.info(
            "ingest_staff_sso_s3: Deactivating accounts %s", created_updated_ids
        )
        models.ActivityStreamStaffSSOUser.objects.exclude(
            id__in=created_updated_ids
        ).update(available=False)


def ingest_activity_stream() -> None:
    logger.info("Starting activity stream ingest")

    created_updated_ids: List[int] = []

    # Create and Update Activity Stream SSO objects
    for activity_stream_object in staff_sso.StaffSSOActivityStreamIterator():
        # Break out if we hit processing limit

        # Only create objects with type of "dit:StaffSSO:User"
        if activity_stream_object["object"]["type"] != "dit:StaffSSO:User":
            continue

        (
            as_staff_sso_user,
            _,
        ) = models.ActivityStreamStaffSSOUser.objects.update_or_create(
            identifier=activity_stream_object["object"]["id"],
            defaults={
                "available": True,
                "name": activity_stream_object["object"]["name"],
                "obj_type": activity_stream_object["object"]["type"],
                "first_name": activity_stream_object["object"][
                    "dit:firstName"  # /PS-IGNORE
                ],
                "last_name": activity_stream_object["object"][
                    "dit:lastName"  # /PS-IGNORE
                ],
                "user_id": activity_stream_object["object"]["dit:StaffSSO:User:userId"],
                "status": activity_stream_object["object"]["dit:StaffSSO:User:status"],
                "last_accessed": activity_stream_object["object"][
                    "dit:StaffSSO:User:lastAccessed"
                ],
                "joined": activity_stream_object["object"]["dit:StaffSSO:User:joined"],
                "email_user_id": activity_stream_object["object"][
                    "dit:StaffSSO:User:emailUserId"
                ],
                "contact_email_address": activity_stream_object["object"][
                    "dit:StaffSSO:User:contactEmailAddress"
                ],
                "became_inactive_on": activity_stream_object["object"][
                    "dit:StaffSSO:User:becameInactiveOn"
                ],
            },
        )

        for email in activity_stream_object["object"]["dit:emailAddress"]:
            models.ActivityStreamStaffSSOUserEmail.objects.get_or_create(
                email_address=email,
                staff_sso_user=as_staff_sso_user,
            )

        created_updated_ids.append(as_staff_sso_user.id)
        logger.info(
            f"Added SSO activity stream record for '{as_staff_sso_user.id}'",
        )

    # Mark the Activity Stream SSO objects that are no longer in the
    # Activity Stream.
    if settings.APP_ENV == "production":
        models.ActivityStreamStaffSSOUser.objects.exclude(
            id__in=created_updated_ids
        ).update(available=False)
