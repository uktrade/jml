from django.urls import reverse

from leavers.models import LeavingRequest


def global_context(request):
    """
    Add global context to all templates.
    Note: remove DEV_LINKS when deploying to production.
    """

    global_context = {
        "COOKIE_RESPONSE": request.COOKIES.get("cookie_banner_response"),
        "DEV_LINKS": [
            (
                "Leaving Requests",
                reverse("flow-list"),
            ),
        ],
    }

    latest_leaving_request = LeavingRequest.objects.all().last()
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
