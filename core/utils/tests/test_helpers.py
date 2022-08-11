from asset_registry.factories import PhysicalAssetFactory, SoftwareAssetFactory
from asset_registry.models import Asset, PhysicalAsset, SoftwareAsset
from django.db.models.query import QuerySet
from django.test import TestCase

from core.utils.helpers import bool_to_yes_no, make_possessive, queryset_to_specific


class BoolToYesNo(TestCase):
    def test_true(self):
        self.assertEqual(bool_to_yes_no(True), "yes")

    def test_false(self):
        self.assertEqual(bool_to_yes_no(False), "no")

    def test_not_boolean(self):
        self.assertEqual(bool_to_yes_no(""), "no")


class MakePossessive(TestCase):
    def test_simple(self):
        self.assertEqual(make_possessive("Bill"), "Bill's")  # /PS-IGNORE

    def test_ends_in_s(self):
        self.assertEqual(make_possessive("Thomas"), "Thomas'")  # /PS-IGNORE


class QuerysetToSpecific(TestCase):
    def setUp(self):
        SoftwareAssetFactory.create_batch(10)
        PhysicalAssetFactory.create_batch(10)

    def test_queryset(self):
        assets: QuerySet[Asset] = Asset.objects.all()
        self.assertEqual(assets.count(), 20)

        for asset in assets:
            self.assertIsInstance(asset, Asset)
            self.assertNotIsInstance(asset, (PhysicalAsset, SoftwareAsset))

    def test_queryset_to_specific(self):
        assets: QuerySet[Asset] = Asset.objects.all()
        self.assertEqual(assets.count(), 20)

        for asset in queryset_to_specific(assets):
            self.assertIsInstance(asset, (PhysicalAsset, SoftwareAsset))
