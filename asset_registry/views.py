from typing import Any, Dict, Optional

from asset_registry.forms import AssetSearchForm
from asset_registry.models import Asset
from django.db.models import QuerySet
from django.http import HttpResponse
from django.views.generic import FormView


class AssetListingView(FormView):
    template_name = "asset_registry/asset_listing.html"
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
        context.update(objects_list=self.get_queryset())
        return context

    def form_valid(self, form) -> HttpResponse:
        self.search_terms = form.cleaned_data["search_terms"]
        return super().render_to_response(self.get_context_data(form=form))
