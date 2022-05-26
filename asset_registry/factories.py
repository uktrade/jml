from datetime import timedelta

import factory
import factory.fuzzy
from asset_registry.models import PysicalAssetCategories, PysicalAssetStatuses
from django.utils import timezone

ONE_DAY = timedelta(days=1)
ONE_YEAR = timedelta(days=365)
TEN_YEARS = timedelta(days=10 * 365)

TEN_YEARS_BEFORE = timezone.now() - TEN_YEARS
ONE_YEAR_BEFORE = timezone.now() - ONE_YEAR
ONE_DAY_AFTER = timezone.now() + ONE_DAY
ONE_YEAR_AFTER = timezone.now() + ONE_YEAR


class AssetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "asset_registry.Asset"


class PhysicalAssetFactory(AssetFactory):
    asset_number = factory.fuzzy.FuzzyText(length=10)
    finance_asset_number = factory.fuzzy.FuzzyDecimal(10000000, 99999999)
    category = factory.fuzzy.FuzzyChoice(choices=PysicalAssetCategories.choices)
    status = factory.fuzzy.FuzzyChoice(choices=PysicalAssetStatuses.choices)
    manufacturer = factory.fuzzy.FuzzyText(length=10)
    model = factory.fuzzy.FuzzyText(length=10)
    serial_number = factory.fuzzy.FuzzyText(length=24)
    purchase_date = factory.fuzzy.FuzzyDate(
        start_date=TEN_YEARS_BEFORE,
        end_date=ONE_YEAR_BEFORE,
    )
    cost = factory.fuzzy.FuzzyFloat(500, 10000)
    warranty_expire_date = factory.fuzzy.FuzzyDate(
        start_date=ONE_YEAR_BEFORE,
        end_date=ONE_YEAR_AFTER,
    )
    location = factory.fuzzy.FuzzyText(length=10)
    address = factory.fuzzy.FuzzyText(length=10)
    date_assigned = factory.fuzzy.FuzzyDate(
        start_date=TEN_YEARS_BEFORE,
        end_date=ONE_YEAR_BEFORE,
    )
    date_returned = factory.fuzzy.FuzzyDate(
        start_date=ONE_YEAR_BEFORE,
        end_date=ONE_DAY_AFTER,
    )
    last_verified_date = factory.fuzzy.FuzzyDate(
        start_date=ONE_YEAR_BEFORE,
        end_date=ONE_DAY_AFTER,
    )

    class Meta:
        model = "asset_registry.PhysicalAsset"


class SoftwareAssetFactory(AssetFactory):

    software_name = factory.fuzzy.FuzzyText(length=50)
    licence_number = factory.fuzzy.FuzzyText(length=50)
    licence_password = factory.fuzzy.FuzzyText(length=50)
    licences_available = factory.fuzzy.FuzzyInteger(10, 1000)
    licences_issued = factory.fuzzy.FuzzyInteger(1, 10)
    renewal_date = factory.fuzzy.FuzzyDate(
        start_date=ONE_YEAR_BEFORE,
        end_date=ONE_YEAR_AFTER,
    )

    class Meta:
        model = "asset_registry.SoftwareAsset"
