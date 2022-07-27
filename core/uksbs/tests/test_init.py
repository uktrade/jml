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

    @override_settings(UKSBS_INTERFACE="core.uksbs.interfaces.UKSBSInterface")
    def test_interface(self):
        self.assertEqual(type(get_uksbs_interface()), UKSBSInterface)
