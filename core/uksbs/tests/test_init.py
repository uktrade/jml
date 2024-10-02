from django.test import TestCase, override_settings

from core.uksbs import get_uksbs_interface
from core.uksbs.interfaces import UKSBSInterface, UKSBSStubbed


@override_settings(
    UKSBS_CLIENT_ID="xxx",
    UKSBS_CLIENT_SECRET="xxx",  # pragma: allowlist secret
    UKSBS_AUTHORISATION_URL="https://fake-uksbs.domain/authorize",
    UKSBS_TOKEN_URL="https://fake-uksbs.domain/getAccessToken",
    UKSBS_HIERARCHY_API_URL="https://fake-uksbs.domain/hierarchy-api/1.0",
    UKSBS_GET_PEOPLE_HIERARCHY="/{person_id}/hierarchy",
    UKSBS_LEAVER_API_URL="https://fake-uksbs.domain/leaver-submission-api/1.0",
    UKSBS_POST_LEAVER_SUBMISSION="/new-leaver",
)
class TestGetUKSBSInterface(TestCase):
    @override_settings(UKSBS_INTERFACE=None)
    def test_not_set(self):
        self.assertEqual(type(get_uksbs_interface()), UKSBSStubbed)

    @override_settings(UKSBS_INTERFACE="core.uksbs.interfaces.UKSBSStubbed")
    def test_stubbed(self):
        self.assertEqual(type(get_uksbs_interface()), UKSBSStubbed)

    @override_settings(
        UKSBS_INTERFACE="core.uksbs.interfaces.UKSBSInterface",
        UKSBS_TOKEN_URL="fake_token_url",
        UKSBS_CLIENT_ID="fake_client_id",
        UKSBS_CLIENT_SECRET="fake_client_secret",  # pragma: allowlist secret
    )
    def test_interface(self):
        self.assertEqual(type(get_uksbs_interface()), UKSBSInterface)
