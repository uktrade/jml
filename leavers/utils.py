from typing import TYPE_CHECKING

from activity_stream.models import ActivityStreamStaffSSOUser
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
