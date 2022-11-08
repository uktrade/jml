import logging
from typing import List

from activity_stream import models, staff_sso

logger = logging.getLogger(__name__)


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
    models.ActivityStreamStaffSSOUser.objects.exclude(
        id__in=created_updated_ids
    ).update(available=False)
