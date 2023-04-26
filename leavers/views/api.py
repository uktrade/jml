import logging

from django.utils.decorators import decorator_from_middleware, method_decorator
from django_hawk.middleware import HawkResponseMiddleware
from django_hawk_drf.authentication import HawkAuthentication
from rest_framework import pagination, permissions, viewsets

from leavers.models import LeavingRequest
from leavers.serializers import LeavingRequestSerializer

logger = logging.getLogger(__name__)


class PrimaryKeyCursorPagination(pagination.CursorPagination):
    ordering = "pk"
    page_size = 10


hawk_response = decorator_from_middleware(HawkResponseMiddleware)


class LeavingRequestViewSetBase(viewsets.ReadOnlyModelViewSet):
    serializer_class = LeavingRequestSerializer
    permission_classes: list[permissions.BasePermission] = []
    pagination_class = PrimaryKeyCursorPagination


@method_decorator(hawk_response, name="list")
@method_decorator(hawk_response, name="retrieve")
class LeavingRequestViewSet(LeavingRequestViewSetBase):
    authentication_classes = [HawkAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    queryset = LeavingRequest.objects.filter(
        cancelled__isnull=True,
        leaver_complete__isnull=False,
    )
