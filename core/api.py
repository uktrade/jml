from dataclasses import dataclass
from typing import Any, List, Optional

from dataclasses_json import DataClassJsonMixin
from django.http import HttpResponseBadRequest
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.utils.decorators import decorator_from_middleware
from django_hawk.middleware import HawkResponseMiddleware
from django_hawk.utils import DjangoHawkAuthenticationFailed, authenticate_request
from rest_framework.views import APIView

from activity_stream.models import ActivityStreamStaffSSOUser
from core.people_finder.interfaces import PersonDetail
from core.people_finder.utils import index_people_finder_result


@dataclass
class IncomingPeopleFinderDetail(DataClassJsonMixin):
    email: str
    first_name: str
    last_name: str
    primary_phone_number: Optional[str]
    grade: Optional[str]
    roles: List[Any]
    photo: Optional[str]


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
        try:
            people_finder_data: IncomingPeopleFinderDetail = (
                IncomingPeopleFinderDetail.from_json(request.body)
            )
        except Exception:
            return HttpResponseBadRequest("Invalid JSON")

        people_finder_email: Optional[str] = people_finder_data.email

        # Validate the data
        if not people_finder_email:
            return HttpResponseBadRequest(
                "No email address found in the people finder data",
            )

        # Check if the email has been ingested from the Activity Stream:
        email_in_activity_stream: bool = ActivityStreamStaffSSOUser.objects.filter(
            email_address=people_finder_email
        ).exists()
        if not email_in_activity_stream:
            # If we can filter the Staff SSO Activity Stream by email,
            # then we should try to do that and ingest the user.
            return HttpResponse(
                "User not found in our stored Staff SSO Activity Stream results",
                status=200,
            )

        job_title: str = ""
        directorate: str = ""
        if people_finder_data.roles:
            job_title = people_finder_data.roles[0]["job_title"]
            directorate = people_finder_data.roles[0]["team"]["name"]

        # Build PersonDetail to be indexed
        person_detail = PersonDetail(
            first_name=people_finder_data.first_name,
            last_name=people_finder_data.last_name,
            image=people_finder_data.photo,
            job_title=job_title,
            directorate=directorate,
            email=people_finder_data.email,
            phone=people_finder_data.primary_phone_number,
            grade=people_finder_data.grade,
        )

        # Update the People Finder details in the Staff index.
        try:
            index_people_finder_result(people_finder_result=person_detail)
        except Exception:
            # We don't mind if the indexing fails as it is possible that
            # someone is updated in People Finder that doesn't exist in the
            # staff index.
            pass

        return HttpResponse("OK", status=200)
