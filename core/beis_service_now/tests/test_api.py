from typing import Dict, List, Optional, Type

from django.test import TestCase, override_settings
from django.urls import reverse

from core.beis_service_now.models import (
    ServiceNowAsset,
    ServiceNowDirectorate,
    ServiceNowObject,
    ServiceNowUser,
)


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
        {},
    ]

    def test_failing_post(self):
        url = self.get_url()
        self.assertFalse(self.model.objects.all().count())

        headers = {"HTTP_X-Api-Key": "some-shared-token"}
        response = self.client.post(
            url,
            data=self.FAILING_POST_DATA,
            content_type="application/json",
            **headers,
        )
        self.assertEqual(response.status_code, 500)

    SUCCESSFUL_POST_DATA: List[Dict[str, str]] = [
        {
            "sys_id": "1234",
        }
    ]

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

    SUCCESSFUL_POST_DATA = [
        {
            "sys_id": "12345",
            "model_category": "Computer",
            "model": "Dell Inc. XPS 13 9380",
            "display_name": "ABCD01234 - Dell Inc. XPS 13 9380",
            "install_status": "In use",
            "substatus": "built",
            "assigned_to": "John Smith",
            "asset_tag": "ABCD01234",  # pragma: allowlist secret
            "serial_number": "1AB2C34",
        }
    ]

    def test_successful_post(self):
        super().test_successful_post()

        assets = self.model.objects.all()
        self.assertEqual(assets.count(), 1)

        asset = assets.first()
        self.assertEqual(asset.sys_id, "12345")


class TestServiceNowUsersApi(ServiceNowApiTestCase):
    url_name = "service-now-api-users"
    model = ServiceNowUser


class TestServiceNowDirectoratesApi(ServiceNowApiTestCase):
    url_name = "service-now-api-directorates"
    model = ServiceNowDirectorate
