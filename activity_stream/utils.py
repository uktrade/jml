import json
import logging

from django.conf import settings

from activity_stream import models
from core.boto_utils import StaffSSOS3Ingest, get_s3_resource

logger = logging.getLogger(__name__)


def staff_sso_s3_to_db(item) -> int:
    user = json.loads(item)
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
            "contact_email_address": user_obj["dit:StaffSSO:User:contactEmailAddress"],
            "became_inactive_on": user_obj["dit:StaffSSO:User:becameInactiveOn"],
        },
    )

    for email in user_obj["dit:emailAddress"]:
        models.ActivityStreamStaffSSOUserEmail.objects.get_or_create(
            email_address=email,
            staff_sso_user=as_staff_sso_user,
        )

    logger.info(
        "ingest_staff_sso_s3: Added SSO activity stream record for %s",
        as_staff_sso_user.id,
    )
    return as_staff_sso_user.id


def ingest_staff_sso_s3() -> None:
    logger.info("ingest_staff_sso_s3: Starting S3 ingest")

    s3_resource = get_s3_resource()
    bucket = s3_resource.Bucket(settings.DATA_FLOW_UPLOADS_BUCKET)

    logger.info("ingest_staff_sso_s3: Reading files from bucket %s", bucket)

    created_updated_ids: list[int] = []

    ingest_manager = StaffSSOS3Ingest()
    for item in ingest_manager.get_data_to_ingest():
        created_updated_id = staff_sso_s3_to_db(item)
        created_updated_ids.append(created_updated_id)

    # Mark the Staff SSO objects that are no longer in the S3 file.
    if settings.APP_ENV == "production":
        logger.info(
            "ingest_staff_sso_s3: Deactivating accounts %s", created_updated_ids
        )
        models.ActivityStreamStaffSSOUser.objects.exclude(
            id__in=created_updated_ids
        ).update(available=False)

    ingest_manager.cleanup()
