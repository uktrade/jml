from asset_registry.views import (
    CreatePhysicalAssetView,
    CreateSoftwareAssetView,
    ListAssetsView,
)
from django.urls import path

urlpatterns = [
    path("", ListAssetsView.as_view(), name="list_assets"),
    path(
        "create-physical/",
        CreatePhysicalAssetView.as_view(),
        name="create_physical_asset",
    ),
    path(
        "create-software/",
        CreateSoftwareAssetView.as_view(),
        name="create_software_asset",
    ),
]
