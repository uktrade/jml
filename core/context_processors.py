from django.conf import settings
from django.urls import reverse

from leavers.models import LeavingRequest


def global_context(request):
    """
    Add global context to all templates.
    Note: remove DEV_LINKS when deploying to production.
    """

    global_context = {
        "COOKIE_RESPONSE": request.COOKIES.get("cookie_banner_response"),
        "DEV_LINKS": [],
    }

    if "dev_tools.apps.DevToolsConfig" in settings.INSTALLED_APPS:
        global_context["DEV_LINKS"].append(
            (
                "Dev tools",
                reverse("dev_tools:index"),
            )
        )

    global_context["DEV_LINKS"].append(
        (
            "Leaving Requests",
            reverse("flow-list"),
        )
    )

    latest_leaving_request = LeavingRequest.objects.filter(
        manager_activitystream_user__email_address=request.user.email
    ).last()
    if latest_leaving_request:
        global_context["DEV_LINKS"].append(
            (
                "Start Line Manager process",
                reverse(
                    "line-manager-start",
                    kwargs={"leaving_request_uuid": latest_leaving_request.uuid},
                ),
            )
        )

    return global_context
