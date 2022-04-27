import logging

from django.conf import settings

logger = logging.getLogger(__name__)


class UKSBSClient:
    def __init__(self) -> None:
        if not settings.UKSBS_API_URL:
            raise ValueError("UKSBS_API_URL is not set")
        self.url = settings.UKSBS_API_URL
