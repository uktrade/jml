import json
import logging
from typing import Any, Dict, Optional, Type

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
    ServiceNowAssetPostBody,
    ServiceNowDirectoratePostBody,
    ServiceNowPostObject,
    ServiceNowUserPostBody,
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
        leaver_complete__isnull=False,
        line_manager_complete__isnull=False,
    )


class DebugApiException(Exception):
    def __init__(self, *args, debug_info: Dict, **kwargs) -> None:
        args = (f"{args[0]} with the debug info: {debug_info}", *args[1:])
        super().__init__(*args, **kwargs)


@method_decorator(csrf_exempt, name="dispatch")
class DebugApiPostView(View):
    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        if not auth_service_now_request(request.headers):
            return HttpResponse(status=403)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request: HttpRequest, **kwargs):
        try:
            api_debug_info = {
                "path": request.get_full_path(),
                "method": request.method,
                "headers": request.headers,
                "GET": request.GET,
                "POST": request.POST,
                "body": request.body,
            }
            raise DebugApiException(
                "POST API endpoint hit",
                debug_info=api_debug_info,
            )
        except Exception as e:
            logger.exception(e)

        return HttpResponse(
            status=200,
            content="Post request logged as an exception in sentry 🙂",
        )


@method_decorator(csrf_exempt, name="dispatch")
class ServiceNowObjectPostView(View):
    model: Optional[Type[ServiceNowObject]] = None

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        if not auth_service_now_request(request.headers):
            return HttpResponse(status=403)
        return super().dispatch(request, *args, **kwargs)

    def ingest_data(self, body: Any) -> None:
        raise NotImplementedError

    def data_to_object(self, obj: ServiceNowObject, data: ServiceNowPostObject) -> None:
        raise NotImplementedError

    def post(self, request: HttpRequest, **kwargs):
        try:
            post_body = json.loads(request.body)
            self.ingest_data(post_body)
        except Exception as e:
            logger.exception(e)
            return HttpResponse(
                status=500,
                content="An error occurred while ingesting the data",
            )
        return HttpResponse(
            status=200,
            content="Post request logged as an exception in sentry 🙂",
        )


class ServiceNowAssetPostView(ServiceNowObjectPostView):
    model = ServiceNowAsset

    def ingest_data(self, body: ServiceNowAssetPostBody) -> None:
        """
        [
            {
                "model_category":"Computer",
                "model":"Dell Inc. XPS 13 9380",
                "display_name":"EUDT01234 - Dell Inc. XPS 13 9380",
                "install_status":"In use",
                "substatus":"built",
                "assigned_to":"John Smith",
                "asset_tag":"EUDT01234",
                "serial_number":"1AB2C34"
            },
            ...
        ]
        """
        for data in body:
            sys_id = data["sys_id"]
            obj, _ = self.model.objects.get_or_create(sys_id=sys_id)
            self.data_to_object(obj, data)

    def data_to_object(self, obj: ServiceNowObject, data: ServiceNowPostObject) -> None:
        # TODO: Update the obj fields from `data`.
        obj.save()


class ServiceNowUserPostView(ServiceNowObjectPostView):
    model = ServiceNowUser

    def ingest_data(self, body: ServiceNowUserPostBody) -> None:
        for data in body:
            sys_id = data["sys_id"]
            obj, _ = self.model.objects.get_or_create(sys_id=sys_id)
            self.data_to_object(obj, data)

    def data_to_object(self, obj: ServiceNowObject, data: ServiceNowPostObject) -> None:
        # TODO: Update the obj fields from `data`.
        obj.save()


class ServiceNowDirectoratePostView(ServiceNowObjectPostView):
    model = ServiceNowDirectorate

    def ingest_data(self, body: ServiceNowDirectoratePostBody) -> None:
        for data in body:
            sys_id = data["sys_id"]
            obj, _ = self.model.objects.get_or_create(sys_id=sys_id)
            self.data_to_object(obj, data)

    def data_to_object(self, obj: ServiceNowObject, data: ServiceNowPostObject) -> None:
        # TODO: Update the obj fields from `data`.
        obj.save()
