import json
import logging
from typing import Iterator

import boto3
from django.conf import settings
from smart_open import open as smart_open

logger = logging.getLogger(__name__)


def get_s3_resource():
    if local_endpoint := getattr(settings, "S3_LOCAL_ENDPOINT_URL", None):
        logger.debug("using local S3 endpoint %s", local_endpoint)
        return boto3.resource(
            "s3",
            endpoint_url=local_endpoint,
            aws_access_key_id="",
            aws_secret_access_key="",
        )

    return boto3.resource("s3")


def get_s3_client():
    if local_endpoint := getattr(settings, "S3_LOCAL_ENDPOINT_URL", None):
        logger.debug("using local S3 endpoint %s", local_endpoint)
        return boto3.client("s3", endpoint_url=local_endpoint)

    return boto3.client("s3")


class JSONLIngest:
    export_bucket: str = settings.DATA_FLOW_UPLOADS_BUCKET
    export_path: str = settings.DATA_FLOW_UPLOADS_BUCKET_PATH
    export_directory: str

    def __init__(self) -> Iterator:
        self.s3_resource = get_s3_resource()
        self.bucket = self.s3_resource.Bucket(self.export_bucket)

    def get_export_path(self):
        return f"{self.export_path}/{self.export_directory}"

    def get_files_to_ingest(self):
        """
        Get all the files that "could" be ingested and order them by last modified date (oldest first)
        """
        logger.info("ingest_staff_sso_s3: Reading files from bucket %s", self.bucket)
        files = self.bucket.objects.filter(Prefix=self.get_export_path())

        sorted_files = sorted(files, key=lambda x: x.last_modified, reverse=False)
        for file in sorted_files:
            file.source_key = f"s3://{file.bucket_name}/{file.key}"
            logger.info(
                "ingest_staff_sso_s3: Found S3 file with key %s", file.source_key
            )

        if len(sorted_files) == 0:
            return []

        return sorted_files

    def process_files(self):
        files = self.get_s3_object_summaries()
        if len(files) == 0:
            logger.info(
                "ingest_staff_sso_s3: No files in bucket %s, stopping task execution",
                self.bucket,
            )
            return

    def get_data_to_ingest(self):
        # Get all files in the export directory
        files_to_process = self.get_files_to_ingest()

        # Select the most recent file
        self.ingest_file = files_to_process[-1]
        self.other_files = files_to_process[:-1]

        # Read the file and yield each line
        with smart_open(
            self.ingest_file.source_key,
            "r",
            transport_params={
                "client": self.s3_resource.meta.client,
            },
            encoding="utf-8",
        ) as file_input_stream:
            logger.info(
                "ingest_staff_sso_s3: Processing file %s", self.ingest_file.source_key
            )
            for line in file_input_stream:
                yield json.loads(line)

    def cleanup(self):
        """
        Delete ingested file and other files in the export directory
        """
        files_to_delete = [self.ingest_file] + self.other_files
        delete_keys = [{"Key": file.key} for file in files_to_delete]

        logger.info("ingest_staff_sso_s3: Deleting keys %s", delete_keys)
        self.bucket.delete_objects(Delete={"Objects": delete_keys})


class PeopleDataS3Ingest(JSONLIngest):
    export_directory = "ExportPeopleDataNewIdentityPipeline/"


class StaffSSOS3Ingest(JSONLIngest):
    export_directory = "StaffSSOUsersPipeline/"
