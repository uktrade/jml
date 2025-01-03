from unittest import mock

from django.test import TestCase, override_settings
from django.utils import timezone

from core.utils.boto import JSONLIngest, get_s3_resource


class TestGetS3Resource(TestCase):
    @override_settings(S3_LOCAL_ENDPOINT_URL=None)
    @mock.patch("boto3.resource")
    def test_no_endpoint_url(self, mock_boto3_resource):
        get_s3_resource()

        mock_boto3_resource.assert_called_once_with("s3")

    @override_settings(S3_LOCAL_ENDPOINT_URL="http://localhost:4566")
    @mock.patch("boto3.resource")
    def test_with_endpoint_url(self, mock_boto3_resource):
        get_s3_resource()

        mock_boto3_resource.assert_called_once_with(
            "s3",
            endpoint_url="http://localhost:4566",
            aws_access_key_id="",
            aws_secret_access_key="",
        )


class TestJSONLIngest(TestCase):
    @mock.patch("boto3.resource")
    def test_get_export_path(self, mock_boto3_resource):
        ingester = JSONLIngest()
        ingester.export_directory = "test/"

        self.assertEqual(
            ingester.get_export_path(),
            "data-flow/exports/local-development/test/",
        )

    @mock.patch("boto3.resource")
    def test_get_files_to_ingest_no_files(
        self,
        mock_boto3_resource,
    ):
        ingester = JSONLIngest()
        ingester.export_directory = "test/"

        self.assertEqual(ingester.get_files_to_ingest(), [])

    @mock.patch("boto3.resource")
    def test_get_files_to_ingest(
        self,
        mock_boto3_resource,
    ):
        file1 = mock.MagicMock(last_modified=timezone.now().isoformat())
        file2 = mock.MagicMock(last_modified=timezone.now().isoformat())
        file3 = mock.MagicMock(last_modified=timezone.now().isoformat())
        mock_boto3_resource.return_value.Bucket.return_value.objects.filter.return_value = [
            file3,
            file2,
            file1,
        ]

        ingester = JSONLIngest()
        ingester.export_directory = "test/"

        self.assertEqual(ingester.get_files_to_ingest(), [file1, file2, file3])

    @mock.patch("boto3.resource")
    def test_cleanup(
        self,
        mock_boto3_resource,
    ):
        mock_boto3_resource.return_value.Bucket.return_value.delete_objects.return_value = None

        file1 = mock.MagicMock(key="file1")
        file2 = mock.MagicMock(key="file2")
        file3 = mock.MagicMock(key="file3")

        ingester = JSONLIngest()
        ingester.ingest_file = file1
        ingester.other_files = [file2, file3]

        ingester.cleanup()

        mock_boto3_resource.return_value.Bucket.return_value.delete_objects.assert_called_once_with(
            Delete={
                "Objects": [
                    {"Key": file1.key},
                    {"Key": file2.key},
                    {"Key": file3.key},
                ]
            }
        )
