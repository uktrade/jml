from django.test import TestCase, override_settings

from core.uksbs import get_uksbs_interface
from core.uksbs.interfaces import UKSBSInterface, UKSBSStubbed


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
