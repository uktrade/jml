import json
from typing import Dict, List, Optional, Type

import pydantic_core
from django.test import TestCase, override_settings
from django.urls import reverse

from core.beis_service_now.models import (
    ServiceNowAsset,
    ServiceNowDirectorate,
    ServiceNowObject,
    ServiceNowUser,
)


def get_object_json(obj_type) -> List[Dict[str, str]]:
    if obj_type not in [
        "assets",
        "directorates",
        "users",
    ]:
        raise ValueError(f"Invalid object type: {obj_type}")
    json_file = f"core/beis_service_now/tests/example_json/{obj_type}.json"
    with open(json_file, "r") as f:
        return json.load(f)


@override_settings(
    BEIS_SERVICE_NOW_AUTH_TOKEN="some-shared-token",
)
class ServiceNowApiTestCase(TestCase):
    url_name: Optional[str] = None
    model: Optional[Type[ServiceNowObject]] = None

    def setUp(self):
        if self.url_name is None:
            self.skipTest("No url_name set for this test case")

    def get_url(self) -> str:
        return reverse(self.url_name)

    EMPTY_POST_DATA: List[Dict[str, str]] = []

    def test_empty_post(self):
        url = self.get_url()
        self.assertFalse(self.model.objects.all().count())

        headers = {"HTTP_X-Api-Key": "some-shared-token"}
        response = self.client.post(
            url,
            data=self.EMPTY_POST_DATA,
            content_type="application/json",
            **headers,
        )

        self.assertEqual(response.status_code, 200)

    FAILING_POST_DATA: List[Dict[str, str]] = [
        {
            "not-real-key": "some-value",
        },
    ]

    def test_failing_post(self):
        url = self.get_url()
        self.assertFalse(self.model.objects.all().count())

        headers = {"HTTP_X-Api-Key": "some-shared-token"}
        with self.assertRaises(pydantic_core.ValidationError):
            self.client.post(
                url,
                data=self.FAILING_POST_DATA,
                content_type="application/json",
                **headers,
            )
        self.assertEqual(self.model.objects.all().count(), 0)

    SUCCESSFUL_POST_DATA: List[Dict[str, str]] = [{}]

    def test_successful_post(self):
        url = self.get_url()
        self.assertFalse(self.model.objects.all().count())

        headers = {"HTTP_X-Api-Key": "some-shared-token"}
        response = self.client.post(
            url,
            data=self.SUCCESSFUL_POST_DATA,
            content_type="application/json",
            **headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.model.objects.all().count())


class TestServiceNowAssetsApi(ServiceNowApiTestCase):
    url_name = "service-now-api-assets"
    model = ServiceNowAsset

    SUCCESSFUL_POST_DATA = get_object_json("assets")

    def test_successful_post(self):
        super().test_successful_post()

        objects = self.model.objects.all()
        self.assertEqual(objects.count(), 3)

        self.assertEqual(objects[0].sys_id, "asset-1")
        self.assertEqual(objects[1].sys_id, "asset-2")
        self.assertEqual(objects[2].sys_id, "asset-3")


class TestServiceNowUsersApi(ServiceNowApiTestCase):
    url_name = "service-now-api-users"
    model = ServiceNowUser

    SUCCESSFUL_POST_DATA = get_object_json("users")

    def test_successful_post(self):
        super().test_successful_post()

        objects = self.model.objects.all()
        self.assertEqual(objects.count(), 4)

        self.assertEqual(objects[0].sys_id, "user-1")
        self.assertEqual(objects[1].sys_id, "user-2")
        self.assertEqual(objects[2].sys_id, "user-3")
        self.assertEqual(objects[3].sys_id, "user-4")


class TestServiceNowDirectoratesApi(ServiceNowApiTestCase):
    url_name = "service-now-api-directorates"
    model = ServiceNowDirectorate

    SUCCESSFUL_POST_DATA = get_object_json("directorates")

    def test_successful_post(self):
        super().test_successful_post()

        objects = self.model.objects.all()
        self.assertEqual(objects.count(), 5)

        self.assertEqual(objects[0].sys_id, "directorate-1")
        self.assertEqual(objects[1].sys_id, "directorate-2")
        self.assertEqual(objects[2].sys_id, "directorate-3")
        self.assertEqual(objects[3].sys_id, "directorate-4")
        self.assertEqual(objects[4].sys_id, "directorate-5")


class TestServiceNowLocationsApi(ServiceNowApiTestCase):
    url_name = "service-now-api-locations"
    model = ServiceNowDirectorate

    SUCCESSFUL_POST_DATA = get_object_json("locations")

    def test_successful_post(self):
        super().test_successful_post()

        objects = self.model.objects.all()
        self.assertEqual(objects.count(), 5)

        self.assertEqual(objects[0].sys_id, "location-1")
        self.assertEqual(objects[1].sys_id, "location-2")
        self.assertEqual(objects[2].sys_id, "location-3")
        self.assertEqual(objects[3].sys_id, "location-4")
        self.assertEqual(objects[4].sys_id, "location-5")
