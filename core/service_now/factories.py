from typing import List

import factory
from factory import fuzzy

from core.service_now import types


class AssetDetails(factory.Factory):
    class Meta:
        model = types.AssetDetails

    sys_id = factory.Sequence(lambda n: n)
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
