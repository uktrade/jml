from typing import List, Optional

from django.conf import settings
from django.db.models import Q
from django.urls import reverse

from core.cookies.views import COOKIE_KEY
from leavers.models import LeavingRequest


def global_context(request):
    """
    Add global context to all templates.
    Note: remove DEV_LINKS when deploying to production.
    """

    global_context = {
        "SERVICE_NAME": "DIT Leaving service",
        "COOKIE_RESPONSE": request.COOKIES.get(COOKIE_KEY),
        "GTM_CODE": settings.GTM_CODE,
        "SERVICE_NOW_OFFLINE_URL": settings.SERVICE_NOW_OFFLINE_URL,
        "DIT_OFFBOARDING_EMAIL": settings.DIT_OFFBOARDING_EMAIL,
        "GPC_RETURN_ADDRESS": settings.GPC_RETURN_ADDRESS,
        "JML_TEAM_CONTACT_EMAIL": settings.JML_TEAM_CONTACT_EMAIL,
        "GETADDRESS_TOKEN": settings.GETADDRESS_TOKEN,
        "DEV_LINKS": [],
        "MAIN_NAV": [],
        "IS_PRODUCTION": bool(settings.APP_ENV == "production"),
    }

    if "dev_tools.apps.DevToolsConfig" in settings.INSTALLED_APPS:
        global_context["DEV_LINKS"].append(
            (
                "Dev tools",
                reverse("dev_tools:index"),
            )
        )

    if request.user.is_authenticated:
        if request.user.is_staff:
            global_context["MAIN_NAV"].append(
                (
                    "Leaving Requests (admin)",
                    reverse("admin-leaving-request-listing"),
                )
            )
            global_context["MAIN_NAV"].append(
                (
                    "Workflows",
                    reverse("flow-list"),
                )
            )
        user_group_names: List[str] = [g.name for g in request.user.groups.all()]
        if "Asset Team" in user_group_names:
            global_context["MAIN_NAV"].append(
                (
                    "Asset Registry",
                    reverse("list-assets"),
                )
            )
        if "SRE" in user_group_names:
            global_context["MAIN_NAV"].append(
                (
                    "Leaving Requests",
                    reverse("sre-listing-incomplete"),
                )
            )
        if "Security Team" in user_group_names:
            global_context["MAIN_NAV"].append(
                (
                    "Leaving Requests",
                    reverse("security-team-listing-incomplete"),
                )
            )

        sso_email_user_id = request.user.sso_email_user_id
        user_is_manager = Q(
            Q(manager_activitystream_user__email_user_id=sso_email_user_id)
            | Q(processing_manager_activitystream_user__email_user_id=sso_email_user_id)
        )

        latest_leaving_request: Optional[LeavingRequest] = (
            LeavingRequest.objects.filter(
                leaver_complete__isnull=False,
                line_manager_complete__isnull=True,
            )
            .filter(user_is_manager)
            .last()
        )
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
