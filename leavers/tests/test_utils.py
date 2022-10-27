from django.test import TestCase, override_settings

from activity_stream.factories import ActivityStreamStaffSSOUserFactory
from leavers.utils.leaving_request import update_or_create_leaving_request
from leavers.utils.security_team import (
    SecuritySubRole,
    get_security_role,
    set_security_role,
)
from user.test.factories import UserFactory


class TestSecurityRole(TestCase):
    def test_set_security_role(self):
        response = self.client.get("/")
        request = response.wsgi_request

        set_security_role(request, SecuritySubRole.BUILDING_PASS)

        self.assertEqual(
            request.session["security_role"], SecuritySubRole.BUILDING_PASS.value
        )

    def test_get_security_role(self):
        response = self.client.get("/")
        request = response.wsgi_request
        request.session["security_role"] = SecuritySubRole.BUILDING_PASS.value
        request.session.save()

        role = get_security_role(request)

        self.assertEqual(role, SecuritySubRole.BUILDING_PASS)

    def test_set_and_get(self):
        response = self.client.get("/")
        request = response.wsgi_request

        set_security_role(request, SecuritySubRole.BUILDING_PASS)
        role = get_security_role(request)

        self.assertEqual(role, SecuritySubRole.BUILDING_PASS)


class TestUpdateOrCreateLeavingRequest(TestCase):
    def setUp(self):
        self.leaver = ActivityStreamStaffSSOUserFactory()
        self.user_requesting = UserFactory()

    def test_update_or_create_leaving_request(self):
        leaving_request = update_or_create_leaving_request(
            leaver=self.leaver,
            user_requesting=self.user_requesting,
        )

        self.assertEqual(leaving_request.user_requesting, self.user_requesting)
        self.assertEqual(leaving_request.leaver_activitystream_user, self.leaver)

    @override_settings(SERVICE_NOW_ENABLE_ONLINE_PROCESS=True)
    def test_service_now_online(self):
        leaving_request = update_or_create_leaving_request(
            leaver=self.leaver,
            user_requesting=self.user_requesting,
        )

        self.assertFalse(leaving_request.service_now_offline)

    @override_settings(SERVICE_NOW_ENABLE_ONLINE_PROCESS=False)
    def test_service_now_offline(self):
        leaving_request = update_or_create_leaving_request(
            leaver=self.leaver,
            user_requesting=self.user_requesting,
        )

        self.assertTrue(leaving_request.service_now_offline)
