from django.conf import settings
from django.shortcuts import redirect
from django.urls import resolve


class DevToolsLoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

        assert settings.APP_ENV in ("local", "dev")

    def __call__(self, request):
        assert hasattr(request, "user")

        if (
            not request.user.is_authenticated
            and resolve(request.path).app_name != "dev_tools"
        ):
            return redirect(settings.LOGIN_URL)

        response = self.get_response(request)

        return response
