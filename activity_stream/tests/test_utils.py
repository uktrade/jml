import datetime
import json
from unittest import mock
from uuid import uuid4

import pytest
from django.test import override_settings

from activity_stream.factories import ActivityStreamStaffSSOUserFactory
from activity_stream.models import (
    ActivityStreamStaffSSOUser,
    ActivityStreamStaffSSOUserEmail,
)
from activity_stream.utils import (
    _get_created_updated_ids,
    _process_staff_sso_file,
    ingest_staff_sso_s3,
)


@pytest.mark.django_db
class TestIngestStaffSSOS3:

    def test_ingest_without_files_processes_nothing_and_doesnt_call_delete(self):
        with mock.patch(
            "activity_stream.utils.get_s3_resource"
        ) as mock_get_s3_resource, mock.patch(
            "activity_stream.utils._get_created_updated_ids"
        ) as mock_get_created_updated_ids:
            ingest_staff_sso_s3()

            mock_get_created_updated_ids.assert_not_called()
            mock_get_s3_resource().Bucket().delete_objects.assert_not_called()

    def test_ingest_with_files_calls_delete_with_all_files(self):
        with mock.patch(
            "activity_stream.utils.get_s3_resource"
        ) as mock_get_s3_resource, mock.patch(
            "activity_stream.utils._do_get_staff_sso_s3_object_summaries"
        ) as mock_get_s3_files, mock.patch(
            "activity_stream.utils._get_created_updated_ids", return_value=1
        ) as mock_get_created_updated_ids:

            mock_get_s3_files.return_value = [
                mock.MagicMock(
                    key="a.jsonl.gz",
                ),
                mock.MagicMock(
                    key="b.jsonl.gz",
                ),
            ]
            mock_get_created_updated_ids.return_value = [1]

            ingest_staff_sso_s3()

            mock_get_s3_resource().Bucket().delete_objects.assert_has_calls(
                [
                    mock.call(
                        Delete={
                            "Objects": [
                                {"Key": "a.jsonl.gz"},
                                {"Key": "b.jsonl.gz"},
                            ]
                        }
                    )
                ]
            )

    def test_ingest_not_in_production_doesnt_set_account_unavailable(self):
        with mock.patch("activity_stream.utils.get_s3_resource"), mock.patch(
            "activity_stream.utils._do_get_staff_sso_s3_object_summaries"
        ) as mock_get_s3_files, mock.patch(
            "activity_stream.utils._get_created_updated_ids", return_value=1
        ) as mock_get_created_updated_ids:

            leaver = ActivityStreamStaffSSOUserFactory(
                identifier=uuid4(), available=True
            )

            mock_get_created_updated_ids.return_value = [leaver.identifier]
            mock_get_s3_files.return_value = [
                mock.MagicMock(
                    source_key="s3://bucket_1/a.jsonl.gz",
                ),
            ]
            ingest_staff_sso_s3()

            assert (
                ActivityStreamStaffSSOUser.objects.filter(identifier=leaver.identifier)
                .first()
                .available
                is True
            )

    @override_settings(APP_ENV="production")
    def test_ingest_not_in_production_sets_account_unavailable(self):
        with mock.patch("activity_stream.utils.get_s3_resource"), mock.patch(
            "activity_stream.utils._do_get_staff_sso_s3_object_summaries"
        ) as mock_get_s3_files, mock.patch(
            "activity_stream.utils._get_created_updated_ids", return_value=1
        ) as mock_get_created_updated_ids:

            leaver = ActivityStreamStaffSSOUserFactory(
                identifier=uuid4(), available=True
            )

            mock_get_created_updated_ids.return_value = [leaver.identifier]
            mock_get_s3_files.return_value = [
                mock.MagicMock(
                    source_key="s3://bucket_1/a.jsonl.gz",
                ),
            ]
            ingest_staff_sso_s3()

            assert (
                ActivityStreamStaffSSOUser.objects.filter(identifier=leaver.identifier)
                .first()
                .available
                is False
            )

    def test_get_created_updated_ids_returns_empty_set_when_no_files(self):
        with mock.patch("activity_stream.utils._process_staff_sso_file"):
            ids = _get_created_updated_ids(
                [],
                mock.MagicMock(),
            )
            assert len(ids) == 0

    def test_get_created_updated_ids_returns_unique_set_when_duplicate_ids_in_files(
        self,
    ):
        with mock.patch(
            "activity_stream.utils._process_staff_sso_file"
        ) as mock_process_staff_sso_file:
            mock_process_staff_sso_file.side_effect = [
                [1, 2, 3, 6, 7, 8],
                [1, 3, 5, 7, 10],
            ]
            ids = _get_created_updated_ids(
                [
                    mock.MagicMock(
                        source_key="s3://bucket_1/a.jsonl.gz",
                    ),
                    mock.MagicMock(
                        source_key="s3://bucket_1/b.jsonl.gz",
                    ),
                ],
                mock.MagicMock(),
            )

            assert len(ids) == 8
            assert ids == [1, 2, 3, 5, 6, 7, 8, 10]

    def test_process_file_empty_file_returns_empty_list_ids(self):
        m_open = mock.mock_open(read_data="\n".join([]))

        with mock.patch(
            "activity_stream.utils.smart_open",
            m_open,
            create=True,
        ):
            ids = _process_staff_sso_file(mock.MagicMock(), mock.MagicMock())
            assert len(ids) == 0

    def test_process_file_adds_new_user(self, sso_user_factory):
        mock_leaver = sso_user_factory()
        m_open = mock.mock_open(
            read_data="\n".join([json.dumps(mock_leaver, default=str)])
        )

        with mock.patch(
            "activity_stream.utils.smart_open",
            m_open,
            create=True,
        ):
            ids = _process_staff_sso_file(mock.MagicMock(), mock.MagicMock())

            leaver = ActivityStreamStaffSSOUser.objects.filter(
                identifier=mock_leaver["object"]["id"]
            ).first()

            leaver_emails = list(
                ActivityStreamStaffSSOUserEmail.objects.filter(staff_sso_user=leaver)
                .all()
                .values_list("email_address", flat=True)
            )

            assert ids == [leaver.id]
            assert set(leaver_emails) == set(mock_leaver["object"]["dit:emailAddress"])

    def test_process_file_updates_existing_user(self, sso_user_factory):
        mock_leaver = sso_user_factory()
        m_open = mock.mock_open(
            read_data="\n".join([json.dumps(mock_leaver, default=str)])
        )

        (leaver, _) = ActivityStreamStaffSSOUser.objects.update_or_create(
            identifier=mock_leaver["object"]["id"],
            defaults={
                "name": "TO BE CHANGED",
                "user_id": "TO BE CHANGED",
                "joined": datetime.datetime.today() - datetime.timedelta(days=3),
            },
        )

        with mock.patch(
            "activity_stream.utils.smart_open",
            m_open,
            create=True,
        ):

            ids = _process_staff_sso_file(mock.MagicMock(), mock.MagicMock())

            reloaded_leaver = ActivityStreamStaffSSOUser.objects.filter(
                id=leaver.id
            ).first()

            assert ids == [reloaded_leaver.id]
            assert reloaded_leaver.name == mock_leaver["object"]["name"]
            assert (
                reloaded_leaver.user_id
                == mock_leaver["object"]["dit:StaffSSO:User:userId"]
            )
            assert (
                reloaded_leaver.joined.strftime("%Y%m%dT%H%M%S.%dZ")
                == mock_leaver["object"]["dit:StaffSSO:User:joined"]
            )
