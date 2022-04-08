from typing import TYPE_CHECKING, Any, Dict, Optional
from uuid import UUID

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
from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.http import Http404, HttpRequest
from django.http.response import HttpResponse, HttpResponseBase
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, FormView, UpdateView

from activity_stream.models import ActivityStreamStaffSSOUser
from core.staff_search.views import StaffSearchView
from core.utils.helpers import queryset_to_specific
from core.utils.staff_index import StaffDocument, get_staff_document_from_staff_index

if TYPE_CHECKING:
    from user.models import User
else:
    User = get_user_model()


def view_asset(request: HttpResponse, pk: int) -> HttpResponse:
    if PhysicalAsset.objects.filter(pk=pk).exists():
        return redirect(reverse("physical-asset", args=[pk]))
    elif SoftwareAsset.objects.filter(pk=pk).exists():
        return redirect(reverse("software-asset", args=[pk]))

    raise Http404


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
        context.update(object_list=queryset_to_specific(self.get_queryset()))
        return context

    def form_valid(self, form) -> HttpResponse:
        self.search_terms = form.cleaned_data["search_terms"]
        return super().render_to_response(self.get_context_data(form=form))


class CreatePhysicalAssetView(CreateView):
    model = PhysicalAsset
    template_name = "asset_registry/physical/create.html"
    form_class = PhysicalAssetCreateForm
    success_url = reverse_lazy("list-assets")


class PhysicalAssetView(UpdateView):
    model = PhysicalAsset
    template_name = "asset_registry/physical/detail.html"
    success_url = reverse_lazy("list-assets")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        success_message, error_message = get_asset_user_action_messages(self.request)

        context.update(
            users=self.object.users.all(),
            success_message=success_message,
            error_message=error_message,
        )

        return context


class UpdatePhysicalAssetView(UpdateView):
    model = PhysicalAsset
    template_name = "asset_registry/physical/update.html"
    form_class = PhysicalAssetUpdateForm

    def get_success_url(self) -> str:
        return reverse("physical-asset", args=[self.object.pk])


class CreateSoftwareAssetView(CreateView):
    model = SoftwareAsset
    template_name = "asset_registry/software/create.html"
    form_class = SoftwareAssetCreateForm
    success_url = reverse_lazy("list-assets")


class SoftwareAssetView(DetailView):
    model = SoftwareAsset
    template_name = "asset_registry/software/detail.html"
    success_url = reverse_lazy("list-assets")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        success_message, error_message = get_asset_user_action_messages(self.request)

        context.update(
            users=self.object.users.all(),
            success_message=success_message,
            error_message=error_message,
        )

        return context


class UpdateSoftwareAssetView(UpdateView):
    model = SoftwareAsset
    template_name = "asset_registry/software/update.html"
    form_class = SoftwareAssetUpdateForm

    def get_success_url(self) -> str:
        return reverse("software-asset", args=[self.object.pk])


class AssetUserSearchView(StaffSearchView):
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
    request: HttpResponse, pk: int, asset_user_uuid: UUID
) -> HttpResponse:
    asset: Asset = get_object_or_404(Asset, pk=pk)
    asset_user_activitystream_user: ActivityStreamStaffSSOUser = get_object_or_404(
        ActivityStreamStaffSSOUser, identifier=asset_user_uuid
    )

    asset.users.remove(asset_user_activitystream_user)

    request.session[
        REMOVE_USER_SUCCESS_SESSION_KEY
    ] = f"{asset_user_activitystream_user.first_name} is no longer associated with this asset."
    return redirect(reverse("view-asset", args=[pk]))


def add_user_to_asset(request: HttpResponse, pk: int) -> HttpResponse:
    return_redirect = redirect(reverse("view-asset", args=[pk]))
    asset = get_object_or_404(Asset, pk=pk)

    asset_user_uuid: Optional[str] = request.GET.get("asset_user_uuid")
    if not asset_user_uuid:
        return return_redirect

    asset_user_staff_document: StaffDocument = get_staff_document_from_staff_index(
        staff_uuid=asset_user_uuid
    )
    try:
        asset_user_activitystream_user = ActivityStreamStaffSSOUser.objects.get(
            identifier=asset_user_staff_document["staff_sso_activity_stream_id"],
        )
    except ActivityStreamStaffSSOUser.DoesNotExist:
        raise Exception("Unable to find user in the Staff SSO ActivityStream.")

    if PhysicalAsset.objects.filter(pk=pk).exists() and asset.users.count() > 1:
        # If the asset is a PhysicalAsset, there can only be one user.
        request.session[ADD_USER_ERROR_SESSION_KEY] = (
            "Physical assets can only have one user. Please remove the current "
            "user before adding a new one."
        )

        return return_redirect

    if asset.users.filter(pk=asset_user_activitystream_user.pk).exists():
        # If the asset already has the user, do nothing.
        request.session[
            ADD_USER_SUCCESS_SESSION_KEY
        ] = f"{asset_user_activitystream_user.first_name} is already associated with this asset."
    else:
        asset.users.add(asset_user_activitystream_user)
        request.session[
            ADD_USER_SUCCESS_SESSION_KEY
        ] = f"{asset_user_activitystream_user.first_name} is now associated with this asset."

    return return_redirect
