from asset_registry.views import (
    CreatePhysicalAssetView,
    CreateSoftwareAssetView,
    ListAssetsView,
    PhysicalAssetView,
    SoftwareAssetView,
    UpdatePhysicalAssetView,
    UpdateSoftwareAssetView,
    update_asset,
)
from django.urls import path

urlpatterns = [
    path("", ListAssetsView.as_view(), name="list_assets"),
    path("update/<int:pk>/", update_asset, name="update_asset"),
    path(
        "physical/create/",
        CreatePhysicalAssetView.as_view(),
        name="create_physical_asset",
    ),
    path(
        "physical/<int:pk>/detail/",
        PhysicalAssetView.as_view(),
        name="physical_asset",
    ),
    path(
        "physical/<int:pk>/update/",
        UpdatePhysicalAssetView.as_view(),
        name="update_physical_asset",
    ),
    path(
        "software/create/",
        CreateSoftwareAssetView.as_view(),
        name="create_software_asset",
    ),
    path(
        "software/<int:pk>/detail/",
        SoftwareAssetView.as_view(),
        name="software_asset",
    ),
    path(
        "software/<int:pk>/update/",
        UpdateSoftwareAssetView.as_view(),
        name="update_software_asset",
    ),
]
