import logging
from abc import ABC, abstractmethod
from typing import Any

from core.uksbs.client import UKSBSClient
from core.uksbs.types import LeavingData

logger = logging.getLogger(__name__)


class UKSBSUserNotFound(Exception):
    pass


class UKSBSBase(ABC):
    @abstractmethod
    def get_user(self, email: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    def submit_leaver_form(self, data: LeavingData) -> None:
        raise NotImplementedError


class UKSBSStubbed(UKSBSBase):
    def get_user(self, email: str) -> Any:
        return None

    def submit_leaver_form(self, data: LeavingData) -> None:
        pass


class UKSBSInterface(UKSBSBase):
    def __init__(self, *args, **kwargs):
        self.client = UKSBSClient()

    def get_user(self, email: str) -> Any:
        return None

    def submit_leaver_form(self, data: LeavingData) -> None:
        pass
