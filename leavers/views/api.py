from django.utils.decorators import decorator_from_middleware, method_decorator
from django_hawk.middleware import HawkResponseMiddleware
from django_hawk_drf.authentication import HawkAuthentication
from rest_framework import pagination, permissions, viewsets

from leavers.models import LeavingRequest
from leavers.serializers import LeavingRequestSerializer


class PrimaryKeyCursorPagination(pagination.CursorPagination):
    ordering = "pk"
    page_size = 10


hawk_response = decorator_from_middleware(HawkResponseMiddleware)


@method_decorator(hawk_response, name="list")
@method_decorator(hawk_response, name="retrieve")
class LeavingRequestViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LeavingRequest.objects.filter(
        cancelled__isnull=True, leaver_complete__isnull=False
    )
    serializer_class = LeavingRequestSerializer
    authentication_classes = [HawkAuthentication]
    permission_classes: list[permissions.BasePermission] = []
    pagination_class = PrimaryKeyCursorPagination
