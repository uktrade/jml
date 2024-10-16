from django.db import models


class ServiceNowObject(models.Model):
    sys_id = models.CharField(max_length=255, primary_key=True)


class ServiceNowAsset(ServiceNowObject):
    ...


class ServiceNowUser(ServiceNowObject):
    email = models.EmailField()

    def get_assets(self) -> list[ServiceNowAsset]:
        # TODO - map assets to users
        # return ServiceNowAsset.objects.filter(assigned_to=self.sys_id)
        return []


class ServiceNowDirectorate(ServiceNowObject):
    ...
