from typing import List

from django.core.management.base import BaseCommand

from activity_stream import models, staff_sso


class Command(BaseCommand):
    help = "Ingest Staff SSO Activity Stream"

    def handle(self, *args, **options):
        created_updated_ids: List[int] = []

        # Create and Update Activity Stream SSO objects
        activity_stream_objects = staff_sso.get_activity_stream()
        for activity_stream_object in activity_stream_objects:
            # Only create objects with type of "dit:StaffSSO:User"
            if activity_stream_object["object"]["type"] != "dit:StaffSSO:User":
                continue

            (
                as_staff_sso_user,
                _,
            ) = models.ActivityStreamStaffSSOUser.objects.get_or_create(
                identifier=activity_stream_object["object"]["id"],
                defaults={
                    "name": activity_stream_object["object"]["name"],
                    "obj_type": activity_stream_object["object"]["type"],
                    "first_name": activity_stream_object["object"][
                        "dit:firstName"  # /PS-IGNORE
                    ],
                    "last_name": activity_stream_object["object"][
                        "dit:lastName"  # /PS-IGNORE
                    ],
                    "email_address": activity_stream_object["object"][
                        "dit:emailAddress"
                    ],
                    "user_id": activity_stream_object["object"][
                        "dit:StaffSSO:User:userId"
                    ],
                    "status": activity_stream_object["object"][
                        "dit:StaffSSO:User:status"
                    ],
                    "last_accessed": activity_stream_object["object"][
                        "dit:StaffSSO:User:lastAccessed"
                    ],
                    "joined": activity_stream_object["object"][
                        "dit:StaffSSO:User:joined"
                    ],
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
            created_updated_ids.append(as_staff_sso_user.id)

        # Delete Activity Stream SSO objects that are no longer in the Activity Stream
        # TODO: I don't think we want to delete any of these as they may be being
        # referenced elsewhere, perhaps we should just mark them as inactive?
        models.ActivityStreamStaffSSOUser.objects.exclude(
            id__in=created_updated_ids
        ).delete()
