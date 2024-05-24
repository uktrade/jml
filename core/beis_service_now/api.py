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
    ServiceNowRITM,
    ServiceNowUser,
)
from core.beis_service_now.serializers import BEISLeavingRequestSerializer
from core.beis_service_now.types import (
    ServiceNowPostAsset,
    ServiceNowPostDirectorate,
    ServiceNowPostLocation,
    ServiceNowPostObject,
    ServiceNowPostRITM,
    ServiceNowPostUser,
)
from core.beis_service_now.utils import json_load_list
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
            and field.concrete
        ]

        logger.info(f"Saving {len(objects_to_save)} {self.model} objects")

        self.model.objects.bulk_update(
            objects_to_save,
            fields=model_update_fields,
        )

    def data_to_object(self, obj: Any, data: Any) -> Any:
        raise NotImplementedError

    def post(self, request: HttpRequest, **kwargs):
        try:
            post_body = json_load_list(request.body)
        except Exception as e:
            logger.exception(e)

            content = (
                "There is an issue with the posted data, please check that it "
                "is valid JSON list"
            )

            if isinstance(e, json.decoder.JSONDecodeError):
                content = f"{content}: {e}"

            return HttpResponse(status=400, content=content)

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
    post_data_class: Type[ServiceNowPostObject] = ServiceNowPostLocation
    sys_id_key = "location_sys_id"

    def data_to_object(
        self, obj: ServiceNowLocation, data: ServiceNowPostLocation
    ) -> ServiceNowLocation:
        obj.name = data.name
        return obj


@method_decorator(csrf_exempt, name="dispatch")
class ServiceNowRITMView(ServiceNowAPIView):
    def post(self, request: HttpRequest, **kwargs):
        try:
            post_body = json_load_list(request.body)
        except Exception as e:
            logger.exception(e)

            content = (
                "There is an issue with the posted data, please check that it "
                "is valid JSON list"
            )

            if isinstance(e, json.decoder.JSONDecodeError):
                content = f"{content}: {e}"

            return HttpResponse(status=400, content=content)

        for ritm in post_body:
            ritm_response = ServiceNowPostRITM(**ritm)
            logger.info(f"RITM response received: {ritm_response.request_id}")
            sn_ritm = ServiceNowRITM.objects.create(
                success=ritm_response.success,
                user_sys_id=ritm_response.user_sys_id,
                request_id=ritm_response.request_id,
            )
            # Find a LeavingRequest for the user_sys_id and add the RITM
            leaving_requests = LeavingRequest.objects.filter(
                service_now_offline=False,
                leaver_complete__isnull=False,
                line_manager_complete__isnull=False,
                leaver_activitystream_user__service_now_users__sys_id=ritm_response.user_sys_id,
            )
            if not leaving_requests.exists():
                logger.exception(
                    Exception(
                        "Can't find a LeavingRequest for the RITM Request: "
                        f"{ritm_response.request_id} and User: "
                        f"{ritm_response.user_sys_id}"
                    )
                )
                continue
            for leaving_request in leaving_requests:
                leaving_request.service_now_ritms.add(sn_ritm)
                leaving_request.save(update_fields=["service_now_ritms"])

        return HttpResponse(
            status=200,
            content="RITM data has been ingested successfully 🎉",
        )
