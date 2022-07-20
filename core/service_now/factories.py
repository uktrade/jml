import factory

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
