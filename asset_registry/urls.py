from asset_registry.views import AssetListingView
from django.urls import path

urlpatterns = [
    path("", AssetListingView.as_view(), name="asset_listing"),
]
