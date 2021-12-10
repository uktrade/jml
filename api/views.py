from api.hawk import (
    HawkAuthentication,
    HawkResponseMiddleware,
)

from django.utils.decorators import decorator_from_middleware

from rest_framework.response import Response
from rest_framework.viewsets import ViewSet


class DetailCorrectionViewSet(
    ViewSet,
):
    authentication_classes = (HawkAuthentication,)
    permission_classes = ()

    @decorator_from_middleware(HawkResponseMiddleware)
    def list(self, request):
        return Response({"implementation": "TODO"})
