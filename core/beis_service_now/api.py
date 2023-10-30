import json
import logging
from typing import Any, Type

from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseBase
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework import pagination, routers
from rest_framework.permissions import IsAuthenticated

from core.beis_service_now.authentication import (
    BEISServiceNowAuthentication,
    auth_service_now_request,
)
from core.beis_service_now.models import (
    ServiceNowAsset,
    ServiceNowDirectorate,
    ServiceNowObject,
    ServiceNowUser,
)
from core.beis_service_now.serializers import BEISLeavingRequestSerializer
from core.beis_service_now.types import (
    ServiceNowObjectPostBody,
    ServiceNowPostAsset,
    ServiceNowPostDirectorate,
    ServiceNowPostUser,
)
from leavers.models import LeavingRequest
from leavers.views.api import LeavingRequestViewSetBase

logger = logging.getLogger(__name__)
router = routers.DefaultRouter()


class PrimaryKeyCursorPagination(pagination.CursorPagination):
    ordering = "pk"
    page_size = 10


class SubmittedLeavingRequestViewSet(LeavingRequestViewSetBase):
    authentication_classes = [BEISServiceNowAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = BEISLeavingRequestSerializer
    queryset = LeavingRequest.objects.filter(
        service_now_offline=False,
        leaver_complete__isnull=False,
        line_manager_complete__isnull=False,
    )

    def get_queryset(self):
        """
        Optionally restricts the returned leaving requests, by filtering
        against a `submitted_from` and `submitted_to` query parameter in the
        URL.
        """
        queryset = super().get_queryset()
        submitted_from = self.request.query_params.get("submitted_from")
        submitted_to = self.request.query_params.get("submitted_to")
        if submitted_from is not None:
            queryset = queryset.filter(line_manager_complete__gte=submitted_from)
        if submitted_to is not None:
            queryset = queryset.filter(line_manager_complete__lte=submitted_to)
        return queryset


@method_decorator(csrf_exempt, name="dispatch")
class ServiceNowObjectPostView(View):
    model: Type[ServiceNowObject] = ServiceNowObject
    sys_id_key: str

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        if not auth_service_now_request(request.headers):
            return HttpResponse(status=403)
        return super().dispatch(request, *args, **kwargs)

    def ingest_data(self, body: ServiceNowObjectPostBody) -> None:
        # TODO: Validate the body before ingesting it (using pydantic?)
        objects_to_save = []
        for data in body:
            sys_id = data[self.sys_id_key]  # type: ignore
            obj, _ = self.model.objects.get_or_create(sys_id=sys_id)
            if not isinstance(obj, ServiceNowObject):
                raise ValueError(
                    f"Expected {self.model} but got {obj} for sys_id {sys_id}"
                )
            updated_obj = self.data_to_object(obj, data)
            objects_to_save.append(updated_obj)

        model_update_fields = [
            field.name
            for field in self.model._meta.get_fields()
            if field.name
            not in [
                "sys_id",
                "servicenowobject_ptr",
                "activity_stream_users",
            ]
        ]

        self.model.objects.bulk_update(
            objects_to_save,
            fields=model_update_fields,
        )

    def data_to_object(self, obj: Any, data: Any) -> Any:
        raise NotImplementedError

    def post(self, request: HttpRequest, **kwargs):
        try:
            post_body = json.loads(request.body)
            self.ingest_data(post_body)
        except Exception as e:
            logger.exception(e)
            return HttpResponse(
                status=500,
                content=f"An error occurred while ingesting the {self.model} data ❌",
            )
        return HttpResponse(
            status=200,
            content=f"{self.model} data has been ingested successfully 🎉",
        )


class ServiceNowAssetPostView(ServiceNowObjectPostView):
    model = ServiceNowAsset
    sys_id_key = "asset_sys_id"

    def data_to_object(
        self, obj: ServiceNowAsset, data: ServiceNowPostAsset
    ) -> ServiceNowAsset:
        obj.model_category = data["model_category"]
        obj.model = data["model"]
        obj.display_name = data["display_name"]
        obj.install_status = data["install_status"]
        obj.substatus = data["substatus"]
        obj.assigned_to_sys_id = data["assigned_to_sys_id"]
        obj.assigned_to_display_name = data["assigned_to_display_name"]
        obj.asset_tag = data["asset_tag"]
        obj.serial_number = data["serial_number"]
        return obj


class ServiceNowUserPostView(ServiceNowObjectPostView):
    model = ServiceNowUser
    sys_id_key = "user_sys_id"

    def data_to_object(
        self, obj: ServiceNowUser, data: ServiceNowPostUser
    ) -> ServiceNowUser:
        obj.user_name = data["user_name"]
        obj.name = data["name"]
        obj.email = data["email"]
        obj.manager_user_name = data["manager_user_name"]
        obj.manager_sys_id = data["manager_sys_id"]
        return obj


class ServiceNowDirectoratePostView(ServiceNowObjectPostView):
    model = ServiceNowDirectorate
    sys_id_key = "directorate_sys_id"

    def data_to_object(
        self, obj: ServiceNowDirectorate, data: ServiceNowPostDirectorate
    ) -> ServiceNowDirectorate:
        obj.name = data["name"]
        return obj
