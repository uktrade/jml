import pytest
from django.test import override_settings

from activity_stream.models import ActivityStreamStaffSSOUser
from activity_stream.utils import ingest_staff_sso_s3
from core.utils.boto import StaffSSOS3Ingest


class TestStaffSSOS3Ingest(StaffSSOS3Ingest):
    def get_files_to_ingest(self):
        return ["1"]


@pytest.mark.django_db
class TestIngestStaffSsoS3:
    @override_settings(S3_LOCAL_ENDPOINT_URL=None)
    def test_no_items(self):
        class Test1StaffSSOS3Ingest(TestStaffSSOS3Ingest):
            def get_data_to_ingest(self):
                return []

        ingest_staff_sso_s3(ingest_manager_class=Test1StaffSSOS3Ingest)

        assert ActivityStreamStaffSSOUser.objects.filter(available=True).count() == 0

    @override_settings(S3_LOCAL_ENDPOINT_URL=None, APP_ENV="production")
    def test_no_files(self, sso_user_factory):
        class Test2StaffSSOS3Ingest(TestStaffSSOS3Ingest):
            def get_files_to_ingest(self):
                return []

            def get_data_to_ingest(self):
                assert False

        ingest_staff_sso_s3(ingest_manager_class=Test2StaffSSOS3Ingest)

        assert ActivityStreamStaffSSOUser.objects.filter(available=True).count() == 0

        class Test3StaffSSOS3Ingest(TestStaffSSOS3Ingest):
            def get_data_to_ingest(self):
                yield sso_user_factory(1)
                yield sso_user_factory(2)

        ingest_staff_sso_s3(ingest_manager_class=Test3StaffSSOS3Ingest)

        assert ActivityStreamStaffSSOUser.objects.filter(available=True).count() == 2

    @override_settings(S3_LOCAL_ENDPOINT_URL=None, APP_ENV="production")
    def test_some_items(self, sso_user_factory):
        class Test4StaffSSOS3Ingest(TestStaffSSOS3Ingest):
            def get_data_to_ingest(self):
                yield sso_user_factory(1)
                yield sso_user_factory(2)
                yield sso_user_factory(3)

        ingest_staff_sso_s3(ingest_manager_class=Test4StaffSSOS3Ingest)

        assert ActivityStreamStaffSSOUser.objects.filter(available=True).count() == 3

        class Test5StaffSSOS3Ingest(TestStaffSSOS3Ingest):
            def get_data_to_ingest(self):
                yield sso_user_factory(1)
                yield sso_user_factory(2)

        ingest_staff_sso_s3(ingest_manager_class=Test5StaffSSOS3Ingest)

        assert ActivityStreamStaffSSOUser.objects.filter(available=True).count() == 2
        assert not ActivityStreamStaffSSOUser.objects.get(user_id=3).available
