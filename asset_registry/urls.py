from asset_registry.views import (
    CreatePhysicalAssetView,
    CreateSoftwareAssetView,
    ListAssetsView,
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
        "physical/update/<int:pk>/",
        UpdatePhysicalAssetView.as_view(),
        name="update_physical_asset",
    ),
    path(
        "software/create/",
        CreateSoftwareAssetView.as_view(),
        name="create_software_asset",
    ),
    path(
        "software/update/<int:pk>/",
        UpdateSoftwareAssetView.as_view(),
        name="update_software_asset",
    ),
]
