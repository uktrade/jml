import boto3
import logging


from django.conf import settings

logger = logging.getLogger(__name__)


def get_s3_resource():
    if settings.S3_LOCAL_ENDPOINT_URL:
        logger.debug("using local S3 endpoint %s", settings.S3_LOCAL_ENDPOINT_URL)
        return boto3.resource("s3", endpoint_url=settings.S3_LOCAL_ENDPOINT_URL)

    return boto3.resource("s3")


def get_s3_client():

    if settings.S3_LOCAL_ENDPOINT_URL:
        logger.debug("using local S3 endpoint %s", settings.S3_LOCAL_ENDPOINT_URL)
        return boto3.client("s3", endpoint_url=settings.S3_LOCAL_ENDPOINT_URL)

    return boto3.client("s3")
