import json
from typing import Optional

from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.utils.decorators import decorator_from_middleware
from django_hawk.middleware import HawkResponseMiddleware
from django_hawk.utils import DjangoHawkAuthenticationFailed, authenticate_request
from rest_framework.views import APIView

from activity_stream.models import ActivityStreamStaffSSOUser
from core.people_finder.interfaces import PersonDetail
from core.people_finder.utils import index_people_finder_result


class PeopleFinderUpdateView(APIView):
    @decorator_from_middleware(HawkResponseMiddleware)
    def post(self, request: HttpRequest) -> HttpResponse:
        """
        Update the people finder data.
        """

        # Try to authenticate with HAWK
        try:
            authenticate_request(request=request)
        except DjangoHawkAuthenticationFailed:
            return HttpResponse(status=401)

        # Get the data
        people_finder_data: PersonDetail = json.loads(request.body)
        people_finder_email: Optional[str] = people_finder_data.get("email")

        # Validate the data
        if not people_finder_email:
            return HttpResponse(
                "No email address found in the people finder data",
                status=400,
            )

        for key, _ in people_finder_data.items():
            if key not in PersonDetail.__required_keys__:
                return HttpResponse(
                    "Invalid key found in the people finder data: {}".format(key),
                    status=400,
                )

        # Check if the email has been ingested from the Activity Stream:
        email_in_activity_stream: bool = ActivityStreamStaffSSOUser.objects.filter(
            email=people_finder_email
        ).exists()
        if not email_in_activity_stream:
            # If we can filter the Staff SSO Activity Stream by email,
            # then we should try to do that and ingest the user.
            return HttpResponse(
                "User not found in our stored Staff SSO Activity Stream results",
                status=200,
            )

        # Update the People Finder details in the Staff index.
        try:
            index_people_finder_result(people_finder_result=people_finder_data)
        except Exception:
            # We don't mind if the indexing fails as it is possible that
            # someone is updated in People Finder that doesn't exist in the
            # staff index.
            pass

        return HttpResponse("OK", status=200)
