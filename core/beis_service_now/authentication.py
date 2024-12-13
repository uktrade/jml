from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http.request import HttpHeaders
from rest_framework.authentication import BaseAuthentication
from rest_framework.request import Request


def auth_service_now_request(request_headers: HttpHeaders) -> bool:
    HEADER_KEY = "X-Api-Key"

    if HEADER_KEY not in request_headers:
        return False
    return request_headers[HEADER_KEY] == settings.BEIS_SERVICE_NOW_AUTH_TOKEN


class APIUser(AnonymousUser):
    """This is a user that is authenticated to use an API endpoint."""

    @property
    def is_authenticated(self):
        return True


class BEISServiceNowAuthentication(BaseAuthentication):
    def get_token(self) -> str:
        return settings.BEIS_SERVICE_NOW_AUTH_TOKEN

    def authenticate(self, request: Request):
        if auth_service_now_request(request.headers):
            return APIUser(), ""
        return None

    def authenticate_header(self, request):
        return ""
