from typing import TYPE_CHECKING, Optional

from django.contrib.auth import get_user_model
from django.db import models

from activity_stream.models import ActivityStreamStaffSSOUser

if TYPE_CHECKING:
    from user.models import User
else:
    User = get_user_model()


class Asset(models.Model):
    users = models.ManyToManyField("activity_stream.ActivityStreamStaffSSOUser")

    class Meta:
        verbose_name = "Asset"
        verbose_name_plural = "Assets"

    def __str__(self) -> str:
        return f"Asset {self.id}"  # type: ignore


class PysicalAssetCategories(models.TextChoices):
    """
    Physical Asset Categories
    """

    AV_EQUIPMENT = "av_equipment", "AV Equipment"
    CAMERA = "camera", "Camera"
    DESKTOP = "desktop", "Desktop"
    LAPTOP = "laptop", "Laptop"
    MIFI_DEVICE = "mifi_device", "Mi-Fi Device"
    MOBILE_SCREEN = "mobile_screen", "Mobile Screen"
    MONITOR = "monitor", "Monitor"
    PORT_REPLICATOR = "port_replicator", "Port Replicator"
    PRINTER = "printer", "Printer"
    SOUND_BAR = "sound_bar", "Sound Bar"
    SPEAKER = "speaker", "Speaker"


class PysicalAssetStatuses(models.TextChoices):
    """
    Physical Asset Statuses
    """

    DEPLOYED = "deployed", "Deployed"
    DISPOSED_OF = "disposed_of", "Disposed Of"
    FAULTY = "faulty", "Faulty"
    HOME_USE = "honme_use", "Home Use"
    LOAN_POOL = "loan_pool", "Loan Pool"
    LOST_STOLEN = "lost_stolen", "Lost/Stolen"
    STOCK = "stock", "Stock"
    WRITTEN_OFF = "written_off", "Written Off Life Expectancy"


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
    date_returned = models.DateField(null=True)
    last_verified_date = models.DateField()

    class Meta:
        verbose_name = "Physical Asset"
        verbose_name_plural = "Physical Assets"

    def __str__(self) -> str:
        return f"Physical Asset {self.id} - {self.asset_number}"  # type: ignore

    @property
    def user(self) -> Optional[ActivityStreamStaffSSOUser]:
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

    def __str__(self) -> str:
        return f"Software Asset {self.id} - {self.software_name}"  # type: ignore
