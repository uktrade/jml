import responses
from django.test import TestCase, override_settings
from django.utils import timezone

from activity_stream.factories import ActivityStreamStaffSSOUserFactory
from core.uksbs.client import UKSBSClient, UKSBSPersonNotFound
from core.uksbs.types import LeavingData, PersonData
from core.uksbs.utils import build_leaving_data_from_leaving_request
from leavers.factories import LeavingRequestFactory
from leavers.forms.line_manager import ReasonForleaving

TODAY = timezone.now()
YESTERDAY = timezone.now() - timezone.timedelta(days=1)
ONE_WEEK_FROM_NOW = TODAY + timezone.timedelta(days=7)

FAKE_PERSON_DATA: PersonData = {
    "person_id": "666",
    "username": "fake_user_1",
    "full_name": "Fake User",
    "first_name": "Fake",
    "last_name": "User",
    "employee_number": "123",
    "department": "DIT",
    "position": "Developer",
    "email_address": "",
    "job_id": 1,
    "work_phone": None,
    "work_mobile": None,
}


@override_settings(
    UKSBS_INTERFACE="core.uksbs.interfaces.UKSBSInterface",
    UKSBS_AUTHORISATION_URL="https://fake-uksbs.domain/authorize",
    UKSBS_TOKEN_URL="https://fake-uksbs.domain/getAccessToken",
    UKSBS_HIERARCHY_API_URL="https://fake-uksbs.domain/hierarchy-api/1.0",
    UKSBS_GET_PEOPLE_HIERARCHY="/{person_id}/hierarchy",
    UKSBS_LEAVER_API_URL="https://fake-uksbs.domain/leaver-submission-api/1.0",
    UKSBS_POST_LEAVER_SUBMISSION="/new-leaver",
)
class TestUKSBSClient(TestCase):
    def test_init(self):
        UKSBSClient()

    @responses.activate
    def test_get_oauth_session(self):
        responses.add(
            responses.POST,
            "https://fake-uksbs.domain/getAccessToken",
            json={
                "access_token": "foo",
                "expires_at": ONE_WEEK_FROM_NOW.timestamp(),
            },
        )

        client = UKSBSClient()
        client.get_oauth_session()

    @responses.activate
    def test_get_oauth_session_with_token(self):
        responses.add(
            responses.POST,
            "https://fake-uksbs.domain/getAccessToken",
            json={
                "access_token": "foo",
                "expires_at": ONE_WEEK_FROM_NOW.timestamp(),
            },
        )

        client = UKSBSClient()
        client.token = {
            "access_token": "foo",
            "expires_at": ONE_WEEK_FROM_NOW.timestamp(),
        }
        client.get_oauth_session()

    @responses.activate
    def test_get_people_hierarchy(self):
        responses.add(
            responses.POST,
            "https://fake-uksbs.domain/getAccessToken",
            json={
                "access_token": "foo",
                "expires_at": ONE_WEEK_FROM_NOW.timestamp(),
            },
        )
        responses.add(
            responses.GET,
            "https://fake-uksbs.domain/hierarchy-api/1.0/666/hierarchy",
            json={
                "items": [
                    {
                        "manager": [],
                        "employee": [FAKE_PERSON_DATA],
                        "report": [],
                    },
                ],
            },
        )

        client = UKSBSClient()
        client.get_people_hierarchy(person_id=666)

    @responses.activate
    def test_get_people_hierarchy_no_person(self):
        responses.add(
            responses.POST,
            "https://fake-uksbs.domain/getAccessToken",
            json={
                "access_token": "foo",
                "expires_at": ONE_WEEK_FROM_NOW.timestamp(),
            },
        )
        responses.add(
            responses.GET,
            "https://fake-uksbs.domain/hierarchy-api/1.0/666/hierarchy",
            json={
                "items": [],
            },
        )

        client = UKSBSClient()
        with self.assertRaises(UKSBSPersonNotFound):
            client.get_people_hierarchy(person_id=666)

    @responses.activate
    def test_post_leaver_form(self):
        leaving_request = LeavingRequestFactory(
            leaving_date=timezone.now(),
            last_day=timezone.now(),
            reason_for_leaving=ReasonForleaving.RESIGNATION.value,
            processing_manager_activitystream_user=ActivityStreamStaffSSOUserFactory(),
        )
        leaver = leaving_request.leaver_activitystream_user
        manager = leaving_request.processing_manager_activitystream_user
        manager_person_data = FAKE_PERSON_DATA.copy()
        manager_person_data["person_id"] = manager.uksbs_person_id

        responses.add(
            responses.POST,
            "https://fake-uksbs.domain/getAccessToken",
            json={
                "access_token": "foo",
                "expires_at": ONE_WEEK_FROM_NOW.timestamp(),
            },
        )
        responses.add(
            responses.GET,
            f"https://fake-uksbs.domain/hierarchy-api/1.0/{leaver.uksbs_person_id}/hierarchy",
            json={
                "items": [
                    {
                        "manager": [manager_person_data],
                        "employee": [FAKE_PERSON_DATA],
                        "report": [FAKE_PERSON_DATA, FAKE_PERSON_DATA],
                    },
                ],
            },
        )
        responses.add(
            responses.POST,
            "https://fake-uksbs.domain/leaver-submission-api/1.0/new-leaver",
            json={},
        )

        leaving_data: LeavingData = build_leaving_data_from_leaving_request(
            leaving_request=leaving_request,
        )

        client = UKSBSClient()
        client.post_leaver_form(data=leaving_data)
