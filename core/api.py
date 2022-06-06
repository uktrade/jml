from django.http.request import HttpRequest
from django.http.response import HttpResponse

from activity_stream.models import ActivityStreamStaffSSOUser
from core.people_finder.interfaces import PersonDetail
from core.people_finder.utils import index_people_finder_result


def people_finder_update(request: HttpRequest) -> HttpResponse:
    """
    Update the people finder data.
    """
    if request.method == "POST":
        people_finder_data: PersonDetail = request.POST.get("people_finder_data")

        # Check if the email has been ingested from the Activity Stream:
        email_in_activity_stream: bool = ActivityStreamStaffSSOUser.objects.filter(
            email=people_finder_data["email"]
        ).exists()
        if not email_in_activity_stream:
            # If we can filter the Staff SSO Activity Stream by email,
            # then we should try to do that and ingest the user.
            return HttpResponse(
                "User not found in our stored Staff SSO Activity Stream results"
            )

        # Update the People Finder details in the Staff index.
        try:
            index_people_finder_result(people_finder_result=people_finder_data)
        except Exception:
            # We don't mind if the indexing fails as it is possible that
            # someone is updated in People Finder that doesn't exist in the
            # staff index.
            pass
        return HttpResponse("OK")
    return HttpResponse(status=400)
