from typing import TYPE_CHECKING, Optional

from django.db import models
from django.utils.functional import cached_property

if TYPE_CHECKING:
    from django.db.models.query import QuerySet


class ServiceNowObject(models.Model):
    sys_id = models.CharField(max_length=255, primary_key=True)

    def __str__(self) -> str:
        return f"{self.sys_id}"


class ServiceNowAsset(ServiceNowObject):
    display_name = models.CharField(max_length=255)
    model_category = models.CharField(max_length=255)
    model = models.CharField(max_length=255)
    install_status = models.CharField(max_length=255)
    substatus = models.CharField(max_length=255)
    asset_tag = models.CharField(max_length=255)
    serial_number = models.CharField(max_length=255)
    assigned_to_sys_id = models.CharField(max_length=255)
    assigned_to_display_name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"{self.display_name} ({self.sys_id})"


class ServiceNowUser(ServiceNowObject):
    user_name = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    manager_user_name = models.CharField(max_length=255)
    manager_sys_id = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"{self.email} ({self.sys_id})"

    @cached_property
    def assets(self) -> "QuerySet[ServiceNowAsset]":
        return ServiceNowAsset.objects.filter(assigned_to_sys_id=self.sys_id)

    @cached_property
    def manager(self) -> Optional["ServiceNowUser"]:
        if not self.manager_sys_id:
            return None
        return ServiceNowUser.objects.get(sys_id=self.manager_sys_id)


class ServiceNowDirectorate(ServiceNowObject):
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"{self.name}"


class ServiceNowLocation(ServiceNowObject):
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"{self.name}"
