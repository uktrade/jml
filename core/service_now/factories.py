from typing import List

import factory
from factory import fuzzy

from core.service_now import types


class AssetDetails(factory.Factory):
    class Meta:
        model = types.AssetDetails

    tag = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: f"Asset {n}")


class LineManagerDetails(factory.Factory):
    class Meta:
        model = types.LineManagerDetails


class Address(factory.Factory):
    class Meta:
        model = types.Address

    building_and_street = factory.Sequence(lambda n: f"Street {n}")
    city = factory.Sequence(lambda n: f"City {n}")
    county = factory.Sequence(lambda n: f"County {n}")
    postcode = factory.Sequence(lambda n: f"PO57 {n}DE")


class LeaverRequestData(factory.Factory):
    class Meta:
        model = types.LeaverRequestData

    collection_address = factory.SubFactory(Address)
    collection_telephone = factory.Sequence(lambda n: f"0123456789{n}")
    collection_email = factory.Sequence(lambda n: f"collection{n}@example.com")
    reason_for_leaving = factory.Sequence(lambda n: f"Reason {n}")
    leaving_date = fuzzy.FuzzyDate(start_date="2022-01-01", end_date="2022-12-31")
    employee_email = factory.Sequence(lambda n: f"employee{n}@example.com")
    employee_name = fuzzy.FuzzyText(length=20)
    employee_department = fuzzy.FuzzyText(length=20)
    employee_directorate = fuzzy.FuzzyText(length=20)
    employee_staff_id = fuzzy.FuzzyText(length=20)
    manager_name = fuzzy.FuzzyText(length=20)
    assets: List[types.AssetDetails] = []
    assets_confirmation = True
    assets_information = ""
