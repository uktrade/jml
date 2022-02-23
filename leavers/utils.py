from typing import TYPE_CHECKING

from django.conf import settings

from activity_stream.models import ActivityStreamStaffSSOUser
from core import notify
from leavers.models import LeavingRequest

if TYPE_CHECKING:
    from user.models import User


def update_or_create_leaving_request(
    *, leaver: ActivityStreamStaffSSOUser, user_requesting: "User", **kwargs
) -> LeavingRequest:
    defaults = {
        "user_requesting": user_requesting,
    }
    defaults.update(**kwargs)

    leaving_request, _ = LeavingRequest.objects.update_or_create(
        leaver_activitystream_user=leaver,
        defaults=defaults,
    )
    return leaving_request


def send_csu4_leaver_email(leaving_request: LeavingRequest):
    """
    Send Cluster 4 Email to notify of a new leaver.

    The data sent in this email is Sensitive and Personal.
    Only add more information to this email if it is absolutely necessary.

    Currently included data:
    - Leaver Name
    """

    if not settings.CSU4_EMAIL:
        raise ValueError("CSU4_EMAIL is not set")

    notify.email(
        email_address=settings.CSU4_EMAIL,
        template_id=notify.EmailTemplates.csu4_leaver_email,
        personalisation={"leaver_name": leaving_request.leaver_name},
    )
