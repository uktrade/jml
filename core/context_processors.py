from typing import List

from django.conf import settings
from django.urls import reverse

from leavers.models import LeavingRequest


def global_context(request):
    """
    Add global context to all templates.
    Note: remove DEV_LINKS when deploying to production.
    """

    global_context = {
        "SERVICE_NAME": "Leaving DIT",
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

    if request.user.is_authenticated:
        user_group_names: List[str] = [g.name for g in request.user.groups.all()]
        if "SRE" in user_group_names:
            global_context["DEV_LINKS"].append(
                (
                    "SRE landing page (complete)",
                    reverse("sre-listing-complete"),
                )
            )
            global_context["DEV_LINKS"].append(
                (
                    "SRE landing page (incomplete)",
                    reverse("sre-listing-incomplete"),
                )
            )
        if "Security Team" in user_group_names:
            global_context["DEV_LINKS"].append(
                (
                    "Security landing page (complete)",
                    reverse("security-team-listing-complete"),
                )
            )
            global_context["DEV_LINKS"].append(
                (
                    "Security landing page (incomplete)",
                    reverse("security-team-listing-incomplete"),
                )
            )

        latest_leaving_request = LeavingRequest.objects.filter(
            leaver_complete__isnull=False,
            manager_activitystream_user__email_address=request.user.email,
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
