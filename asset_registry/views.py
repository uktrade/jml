from typing import Any, Dict, Optional

from asset_registry.forms import (
    AssetSearchForm,
    PhysicalAssetCreateForm,
    SoftwareAssetCreateForm,
)
from asset_registry.models import Asset, PhysicalAsset, SoftwareAsset
from django.db.models import QuerySet
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView


class ListAssetsView(FormView):
    template_name = "asset_registry/list_assets.html"
    form_class = AssetSearchForm
    search_terms: Optional[str] = None

    def get_queryset(self) -> QuerySet:
        queryset = Asset.objects.all()
        if self.search_terms:
            # TODO: implement search
            pass
        return queryset

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(object_list=self.get_queryset())
        return context

    def form_valid(self, form) -> HttpResponse:
        self.search_terms = form.cleaned_data["search_terms"]
        return super().render_to_response(self.get_context_data(form=form))


class CreatePhysicalAssetView(CreateView):
    model = PhysicalAsset
    template_name = "asset_registry/create_physical_asset.html"
    form_class = PhysicalAssetCreateForm
    success_url = reverse_lazy("list_assets")


class CreateSoftwareAssetView(CreateView):
    model = SoftwareAsset
    template_name = "asset_registry/create_software_asset.html"
    form_class = SoftwareAssetCreateForm
    success_url = reverse_lazy("list_assets")
