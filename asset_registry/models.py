from typing import TYPE_CHECKING, Optional

from django.contrib.auth import get_user_model
from django.db import models

if TYPE_CHECKING:
    from user.models import User
else:
    User = get_user_model()


class Asset(models.Model):
    users = models.ManyToManyField("user.User")

    class Meta:
        verbose_name = "Asset"
        verbose_name_plural = "Assets"


class PysicalAssetCategories(models.TextChoices):
    """
    Physical Asset Categories
    """

    pass


class PysicalAssetStatuses(models.TextChoices):
    """
    Physical Asset Statuses
    """

    pass


class PhysicalAsset(Asset):
    asset_number = models.CharField(max_length=50, unique=True)
    finance_asset_number = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=50, choices=PysicalAssetCategories.choices)
    status = models.CharField(max_length=50, choices=PysicalAssetStatuses.choices)
    manufacturer = models.CharField(max_length=255)
    model = models.CharField(max_length=255)
    serial_number = models.CharField(max_length=255)
    purchase_date = models.DateField()
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    warranty_expire_date = models.DateField()
    location = models.CharField(max_length=50)
    address = models.CharField(max_length=50)
    date_assigned = models.DateField()
    date_returned = models.DateField()
    last_verified_date = models.DateField()

    class Meta:
        verbose_name = "Physical Asset"
        verbose_name_plural = "Physical Assets"

    @property
    def user(self) -> Optional[User]:
        return self.users.first()


class SoftwareAsset(Asset):
    software_name = models.CharField(max_length=50)
    licence_number = models.CharField(max_length=50)
    licence_password = models.CharField(max_length=50)  # Encrypt????
    licences_available = models.IntegerField()
    licences_issued = models.IntegerField()
    renewal_date = models.DateField()

    class Meta:
        verbose_name = "Software Asset"
        verbose_name_plural = "Software Assets"
