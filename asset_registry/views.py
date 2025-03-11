from typing import TYPE_CHECKING, Any, Dict, List, Optional
from uuid import UUID

from django.contrib.auth import get_user_model
from django.contrib.postgres.search import SearchVector
from django.db.models.query import QuerySet
from django.http import Http404, HttpRequest, HttpResponseForbidden
from django.http.response import HttpResponse, HttpResponseBase
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, FormView, UpdateView

from activity_stream.models import ActivityStreamStaffSSOUser
from asset_registry.forms import (
    AssetSearchForm,
    PhysicalAssetCreateForm,
    PhysicalAssetUpdateForm,
    SoftwareAssetCreateForm,
    SoftwareAssetUpdateForm,
)
from asset_registry.models import Asset, PhysicalAsset, SoftwareAsset
from asset_registry.utils import (
    ADD_USER_ERROR_SESSION_KEY,
    ADD_USER_SUCCESS_SESSION_KEY,
    REMOVE_USER_SUCCESS_SESSION_KEY,
    get_asset_user_action_messages,
)
from core.staff_search.views import StaffSearchView
from core.utils.staff_index import StaffDocument, get_staff_document_from_staff_index
from core.views import BaseTemplateView

if TYPE_CHECKING:
    from user.models import User
else:
    User = get_user_model()


def user_in_asset_group(*, request: HttpRequest) -> bool:
    if not request.user.is_authenticated:
        return False

    user_in_asset_team: bool = request.user.groups.filter(
        name="Asset Team",
    ).exists()

    return user_in_asset_team


def view_asset(request: HttpRequest, pk: int) -> HttpResponse:
    if not user_in_asset_group(request=request):
        return HttpResponseForbidden()

    if PhysicalAsset.objects.filter(pk=pk).exists():
        return redirect(reverse("physical-asset", args=[pk]))
    elif SoftwareAsset.objects.filter(pk=pk).exists():
        return redirect(reverse("software-asset", args=[pk]))

    raise Http404


class AssetViewMixin:
    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        if not user_in_asset_group(request=request):
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)  # type: ignore


class ListAssetsView(AssetViewMixin, FormView, BaseTemplateView):
    template_name = "asset_registry/list_assets.html"
    form_class = AssetSearchForm
    search_terms: Optional[str] = None

    def get_queryset(self) -> QuerySet:
        queryset: QuerySet[Asset] = Asset.objects.all()
        if self.search_terms:
            asset_ids: List[int] = []

            physical_asset_queryset: QuerySet[PhysicalAsset] = (
                PhysicalAsset.objects.all().annotate(
                    search=SearchVector(
                        "users__name",
                        "users__first_name",
                        "users__last_name",
                        "users__email_address",
                        "asset_number",
                        "finance_asset_number",
                        "category",
                        "status",
                        "manufacturer",
                        "model",
                        "serial_number",
                    )
                )
            )
            physical_asset_queryset = physical_asset_queryset.filter(
                search=self.search_terms
            )
            asset_ids += physical_asset_queryset.values_list("id", flat=True)

            software_asset_queryset: QuerySet[SoftwareAsset] = (
                SoftwareAsset.objects.all().annotate(
                    search=SearchVector(
                        "users__name",
                        "users__first_name",
                        "users__last_name",
                        "users__email_address",
                        "software_name",
                        "licence_number",
                    )
                )
            )
            software_asset_queryset = software_asset_queryset.filter(
                search=self.search_terms
            )
            asset_ids += software_asset_queryset.values_list("id", flat=True)
            queryset = queryset.filter(id__in=asset_ids)
        return queryset

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(object_list=self.get_queryset())
        return context

    def form_valid(self, form) -> HttpResponse:
        self.search_terms = form.cleaned_data["search_terms"]
        return super().render_to_response(self.get_context_data(form=form))


class CreatePhysicalAssetView(AssetViewMixin, CreateView, BaseTemplateView):
    model = PhysicalAsset
    template_name = "asset_registry/physical/create.html"
    form_class = PhysicalAssetCreateForm
    success_url = reverse_lazy("list-assets")


class PhysicalAssetView(AssetViewMixin, DetailView, BaseTemplateView):
    model = PhysicalAsset
    template_name = "asset_registry/physical/detail.html"
    back_link_url = reverse_lazy("list-assets")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        obj = self.object  # type: ignore
        context = super().get_context_data(**kwargs)

        success_message, error_message = get_asset_user_action_messages(self.request)

        context.update(
            users=obj.users.all(),
            success_message=success_message,
            error_message=error_message,
        )

        return context


class UpdatePhysicalAssetView(AssetViewMixin, UpdateView, BaseTemplateView):
    model = PhysicalAsset
    template_name = "asset_registry/physical/update.html"
    form_class = PhysicalAssetUpdateForm

    def get_success_url(self) -> str:
        obj = self.object  # type: ignore
        return reverse("physical-asset", args=[obj.pk])


class CreateSoftwareAssetView(AssetViewMixin, CreateView, BaseTemplateView):
    model = SoftwareAsset
    template_name = "asset_registry/software/create.html"
    form_class = SoftwareAssetCreateForm
    success_url = reverse_lazy("list-assets")


class SoftwareAssetView(AssetViewMixin, DetailView, BaseTemplateView):
    model = SoftwareAsset
    template_name = "asset_registry/software/detail.html"
    back_link_url = reverse_lazy("list-assets")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        obj = self.object  # type: ignore
        context = super().get_context_data(**kwargs)

        success_message, error_message = get_asset_user_action_messages(self.request)

        context.update(
            users=obj.users.all(),
            success_message=success_message,
            error_message=error_message,
        )

        return context


class UpdateSoftwareAssetView(AssetViewMixin, UpdateView, BaseTemplateView):
    model = SoftwareAsset
    template_name = "asset_registry/software/update.html"
    form_class = SoftwareAssetUpdateForm

    def get_success_url(self) -> str:
        obj = self.object  # type: ignore
        return reverse("software-asset", args=[obj.pk])


class AssetUserSearchView(AssetViewMixin, StaffSearchView):
    query_param_name = "asset_user_uuid"
    search_name = "asset user"

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        self.asset = get_object_or_404(Asset, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self) -> str:
        return reverse("add-user-to-asset", args=[self.asset.pk])


def remove_user_from_asset(
    request: HttpRequest, pk: int, asset_user_uuid: UUID
) -> HttpResponse:
    asset: Asset = get_object_or_404(Asset, pk=pk)
    asset_user_activitystream_user: ActivityStreamStaffSSOUser = get_object_or_404(
        ActivityStreamStaffSSOUser, identifier=asset_user_uuid
    )

    if not user_in_asset_group(request=request):
        return HttpResponseForbidden()

    asset.users.remove(asset_user_activitystream_user)

    request.session[REMOVE_USER_SUCCESS_SESSION_KEY] = (
        f"{asset_user_activitystream_user.first_name} is no longer associated with this asset."
    )
    return redirect(reverse("view-asset", args=[pk]))


def add_user_to_asset(request: HttpRequest, pk: int) -> HttpResponse:
    return_redirect = redirect(reverse("view-asset", args=[pk]))
    asset = get_object_or_404(Asset, pk=pk)

    if not user_in_asset_group(request=request):
        return HttpResponseForbidden()

    asset_user_uuid: Optional[str] = request.GET.get("asset_user_uuid")
    if not asset_user_uuid:
        return return_redirect

    asset_user_staff_document: StaffDocument = get_staff_document_from_staff_index(
        staff_uuid=asset_user_uuid
    )
    try:
        asset_user_activitystream_user = (
            ActivityStreamStaffSSOUser.objects.active().get(
                identifier=asset_user_staff_document.staff_sso_activity_stream_id,
            )
        )
    except ActivityStreamStaffSSOUser.DoesNotExist:
        raise Exception("Unable to find user in the Staff SSO ActivityStream.")

    if asset.users.filter(pk=asset_user_activitystream_user.pk).exists():
        # If the asset already has the user, do nothing.
        request.session[ADD_USER_SUCCESS_SESSION_KEY] = (
            f"{asset_user_activitystream_user.first_name} is already associated with this asset."
        )

        return return_redirect

    if PhysicalAsset.objects.filter(pk=pk).exists() and asset.users.count() >= 1:
        # If the asset is a PhysicalAsset, there can only be one user.
        request.session[ADD_USER_ERROR_SESSION_KEY] = (
            "Physical assets can only have one user. Please remove the current "
            "user before adding a new one."
        )

        return return_redirect

    asset.users.add(asset_user_activitystream_user)
    request.session[ADD_USER_SUCCESS_SESSION_KEY] = (
        f"{asset_user_activitystream_user.first_name} is now associated with this asset."
    )

    return return_redirect


class UserAssetView(AssetViewMixin, DetailView, BaseTemplateView):
    model = ActivityStreamStaffSSOUser
    template_name = "asset_registry/user.html"
    slug_field = "identifier"
    slug_url_kwarg = "asset_user_uuid"
    back_link_url = reverse_lazy("list-assets")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        obj = self.object  # type: ignore
        context = super().get_context_data(**kwargs)
        assets = Asset.objects.filter(users__pk=obj.pk)
        context.update(assets=assets)
        return context
