import json

import mohawk
from django.test import TestCase, override_settings
from django.urls import reverse

PEOPLE_FINDER_EXAMPLE_POST = {
    "people_finder_id": 1,
    "staff_sso_id": "1111a111-11a1-1a1a-a1a1-aaaa1a1a1aa1",  # /PS-IGNORE
    "email": "john.smith@example.com",  # /PS-IGNORE
    "contact_email": None,
    "full_name": "John Smith",  # /PS-IGNORE
    "first_name": "John",
    "last_name": "Smith",
    "profile_url": "http://example.com/profile-url/",
    "roles": [],
    "formatted_roles": [],
    "manager_people_finder_id": None,
    "completion_score": 55,
    "is_stale": False,
    "works_monday": False,
    "works_tuesday": False,
    "works_wednesday": False,
    "works_thursday": False,
    "works_friday": False,
    "works_saturday": False,
    "works_sunday": False,
    "primary_phone_number": None,
    "secondary_phone_number": None,
    "formatted_location": None,
    "buildings": [],
    "formatted_buildings": "",
    "city": None,
    "country": "GB",
    "country_name": "United Kingdom",
    "grade": None,
    "formatted_grade": None,
    "location_in_building": None,
    "location_other_uk": None,
    "location_other_overseas": None,
    "key_skills": [],
    "other_key_skills": None,
    "formatted_key_skills": "",
    "learning_and_development": [],
    "other_learning_and_development": None,
    "formatted_learning_and_development": "",
    "networks": [],
    "formatted_networks": "",
    "professions": [],
    "formatted_professions": "",
    "additional_responsibilities": [],
    "other_additional_responsibilities": None,
    "formatted_additional_responsibilities": "",
    "language_fluent": None,
    "language_intermediate": None,
    "created_at": "2022-06-13T15:10:11.289114Z",
    "last_edited_or_confirmed_at": "2022-06-13T15:10:11.288698Z",
    "login_count": 1,
    "last_login_at": "2022-06-13T15:10:16.629980Z",
    "slug": "aaaa1aa1-1aa1-1aaa-1a11-1a111a111a11",
    "manager_slug": None,
    "legacy_people_finder_slug": None,
    "photo": None,
    "photo_small": None,
}


def hawk_auth_sender(
    url: str,
    key_id: str = "some-id",
    secret_key: str = "some-secret",
    method: str = "POST",
    content: str = "",
    content_type: str = "",
):
    credentials = {
        "id": key_id,
        "key": secret_key,
        "algorithm": "sha256",
    }
    return mohawk.Sender(
        credentials,
        url,
        method,
        content=content,
        content_type=content_type,
    )


@override_settings(
    DJANGO_HAWK={
        "HAWK_INCOMING_ACCESS_KEY": "some-id",
        "HAWK_INCOMING_SECRET_KEY": "some-secret",
    }
)
class TestPeopleFinderUpdateView(TestCase):
    view_name = "people-finder-update"

    def get_path(self) -> str:
        return reverse(self.view_name)

    def get_url(self) -> str:
        return "http://testserver" + self.get_path()

    def test_post_invalid_auth(self):
        url = self.get_url()
        content = json.dumps(PEOPLE_FINDER_EXAMPLE_POST)
        sender = hawk_auth_sender(
            url=url,
            content_type="json",
            content=content,
            key_id="invalid-id",
            secret_key="invalid-secret",
        )
        response = self.client.post(
            url,
            content_type="json",
            data=content,
            HTTP_AUTHORIZATION=sender.request_header,
            HTTP_X_FORWARDED_FOR="1.2.3.4, 123.123.123.123",
        )

        self.assertEqual(response.status_code, 401)

    def test_post(self):
        url = self.get_url()
        content = json.dumps(PEOPLE_FINDER_EXAMPLE_POST)
        sender = hawk_auth_sender(
            url=url,
            content_type="json",
            content=content,
        )
        response = self.client.post(
            url,
            content_type="json",
            data=content,
            HTTP_AUTHORIZATION=sender.request_header,
            HTTP_X_FORWARDED_FOR="1.2.3.4, 123.123.123.123",
        )

        self.assertEqual(response.status_code, 200)

    def test_post_bad_data(self):
        url = self.get_url()
        content = "{}"
        sender = hawk_auth_sender(
            url=url,
            content_type="json",
            content=content,
        )
        response = self.client.post(
            url,
            content_type="json",
            data=content,
            HTTP_AUTHORIZATION=sender.request_header,
            HTTP_X_FORWARDED_FOR="1.2.3.4, 123.123.123.123",
        )

        self.assertEqual(response.status_code, 400)
