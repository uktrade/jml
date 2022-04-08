from asset_registry.views import (
    AssetUserSearchView,
    CreatePhysicalAssetView,
    CreateSoftwareAssetView,
    ListAssetsView,
    PhysicalAssetView,
    SoftwareAssetView,
    UpdatePhysicalAssetView,
    UpdateSoftwareAssetView,
    add_user_to_asset,
    view_asset,
)
from django.urls import path

urlpatterns = [
    path("", ListAssetsView.as_view(), name="list-assets"),
    path(
        "<int:pk>/user-search/",
        AssetUserSearchView.as_view(),
        name="asset-user-search",
    ),
    path("<int:pk>/", view_asset, name="view-asset"),
    path("<int:pk>/add-user/", add_user_to_asset, name="add-user-to-asset"),
    path(
        "physical/create/",
        CreatePhysicalAssetView.as_view(),
        name="create-physical-asset",
    ),
    path(
        "physical/<int:pk>/detail/",
        PhysicalAssetView.as_view(),
        name="physical-asset",
    ),
    path(
        "physical/<int:pk>/update/",
        UpdatePhysicalAssetView.as_view(),
        name="update-physical-asset",
    ),
    path(
        "software/create/",
        CreateSoftwareAssetView.as_view(),
        name="create-software-asset",
    ),
    path(
        "software/<int:pk>/detail/",
        SoftwareAssetView.as_view(),
        name="software-asset",
    ),
    path(
        "software/<int:pk>/update/",
        UpdateSoftwareAssetView.as_view(),
        name="update-software-asset",
    ),
]
