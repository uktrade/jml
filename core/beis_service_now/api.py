import json
import logging
from typing import Any, Dict, List, Type

import pydantic_core
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
    ServiceNowLocation,
    ServiceNowObject,
    ServiceNowUser,
)
from core.beis_service_now.serializers import BEISLeavingRequestSerializer
from core.beis_service_now.types import (
    ServiceNowPostAsset,
    ServiceNowPostDirectorate,
    ServiceNowPostLocation,
    ServiceNowPostObject,
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
class ServiceNowAPIView(View):
    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        if not auth_service_now_request(request.headers):
            logger.warning("ServiceNow request failed authentication")
            return HttpResponse(status=403)
        logger.warning("ServiceNow request succeeded authentication")
        return super().dispatch(request, *args, **kwargs)


class ServiceNowObjectPostView(ServiceNowAPIView):
    model: Type[ServiceNowObject] = ServiceNowObject
    post_data_class: Type[ServiceNowPostObject] = ServiceNowPostObject
    sys_id_key: str

    def ingest_data(self, body: List[Dict]) -> None:
        objects_to_save = []
        for data in body:
            sn_post_data = self.post_data_class(**data)

            sys_id = getattr(sn_post_data, self.sys_id_key)
            if not sys_id:
                raise ValueError(
                    f"Expected {self.sys_id_key} in {self.post_data_class} but got {sys_id}"
                )

            obj, _ = self.model.objects.get_or_create(sys_id=sys_id)
            if not isinstance(obj, ServiceNowObject):
                raise ValueError(
                    f"Expected {self.model} but got {obj} for sys_id {sys_id}"
                )

            updated_obj = self.data_to_object(obj, sn_post_data)

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

        logger.info(f"Saving {len(objects_to_save)} {self.model} objects")

        self.model.objects.bulk_update(
            objects_to_save,
            fields=model_update_fields,
        )

    def data_to_object(self, obj: Any, data: Any) -> Any:
        raise NotImplementedError

    def post(self, request: HttpRequest, **kwargs):
        body = request.body.decode()

        # NOTE: This is a hack to remove the quotes from the body since the
        # ServiceNow request sends the body as a string.
        if body.startswith('"') and body.endswith('"'):
            body = body[1:-1]

        try:
            post_body = json.loads(body)
        except json.decoder.JSONDecodeError as e:
            logger.exception(e)
            return HttpResponse(
                status=400,
                content=(
                    "There is an issue with the posted data, please check that"
                    f" it is valid JSON: {e}"
                ),
            )
        except Exception as e:
            logger.exception(e)
            return HttpResponse(
                status=400,
                content=(
                    "There is an issue with the posted data, please check that"
                    " it is valid JSON"
                ),
            )

        # TODO: Remove this debug exception
        debug_exception = Exception(
            f"""
            POST request received!

            post_body: {post_body}
            """
        )
        logger.exception(debug_exception)

        if not isinstance(post_body, list):
            logger.error(f"Expected a list of objects, got {type(post_body)}")
            return HttpResponse(
                status=400,
                content=(
                    "There is an issue with the posted data, please check that"
                    " it is a list of objects"
                ),
            )

        try:
            self.ingest_data(post_body)
        except pydantic_core.ValidationError as e:
            logger.exception(e)
            raise e
        except Exception as e:
            logger.exception(e)
            return HttpResponse(
                status=500,
                content=f"An error occurred while ingesting the {self.model} data ❌",
            )
        logger.info(f"Successfully ingested {self.model} data ✅")
        return HttpResponse(
            status=200,
            content=f"{self.model} data has been ingested successfully 🎉",
        )


class ServiceNowAssetPostView(ServiceNowObjectPostView):
    model = ServiceNowAsset
    post_data_class: Type[ServiceNowPostObject] = ServiceNowPostAsset
    sys_id_key = "asset_sys_id"

    def data_to_object(
        self, obj: ServiceNowAsset, data: ServiceNowPostAsset
    ) -> ServiceNowAsset:
        obj.model_category = data.model_category
        obj.model = data.model
        obj.display_name = data.display_name
        obj.install_status = data.install_status
        obj.substatus = data.substatus
        obj.assigned_to_sys_id = data.assigned_to_sys_id
        obj.assigned_to_display_name = data.assigned_to_display_name
        obj.asset_tag = data.asset_tag
        obj.serial_number = data.serial_number
        return obj


class ServiceNowUserPostView(ServiceNowObjectPostView):
    model = ServiceNowUser
    post_data_class: Type[ServiceNowPostObject] = ServiceNowPostUser
    sys_id_key = "user_sys_id"

    def data_to_object(
        self, obj: ServiceNowUser, data: ServiceNowPostUser
    ) -> ServiceNowUser:
        obj.user_name = data.user_name
        obj.name = data.name
        obj.email = data.email
        obj.manager_user_name = data.manager_user_name
        obj.manager_sys_id = data.manager_sys_id
        return obj


class ServiceNowDirectoratePostView(ServiceNowObjectPostView):
    model = ServiceNowDirectorate
    post_data_class: Type[ServiceNowPostObject] = ServiceNowPostDirectorate
    sys_id_key = "directorate_sys_id"

    def data_to_object(
        self, obj: ServiceNowDirectorate, data: ServiceNowPostDirectorate
    ) -> ServiceNowDirectorate:
        obj.name = data.name
        return obj


class ServiceNowLocationPostView(ServiceNowObjectPostView):
    model = ServiceNowLocation
    post_data_class: Type[ServiceNowPostObject] = ServiceNowPostDirectorate
    sys_id_key = "location_sys_id"

    def data_to_object(
        self, obj: ServiceNowLocation, data: ServiceNowPostLocation
    ) -> ServiceNowLocation:
        obj.name = data.name
        return obj


@method_decorator(csrf_exempt, name="dispatch")
class ServiceNowRITMView(ServiceNowAPIView):
    def post(self, request: HttpRequest, **kwargs):
        post_body = json.loads(request.body)

        # Raise and log an exception for debugging
        try:
            raise Exception(f"RITM response received: {post_body}")
        except Exception as e:
            logger.exception(e)

        return HttpResponse(
            status=200,
            content="RITM response stored!",
        )
