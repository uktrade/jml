from typing import Any, Dict

from django.http import HttpResponse, JsonResponse
from django.template.response import TemplateResponse

from health_check.mixins import CheckMixin
from health_check.views import MainView


class CustomHealthCheckView(MainView):
    template_name = "core_health_check/index.html"
    title: str = "System status"

    def render_to_response(
        self, context: Dict[str, Any], status: int, **response_kwargs: Any
    ) -> HttpResponse:
        if status == 500:
            status = 503
        return super().render_to_response(context, status=status, **response_kwargs)

    def render_to_response_json(self, plugins: Any, status: int) -> JsonResponse:
        if status == 500:
            status = 503
        return super().render_to_response_json(plugins, status)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(title=self.title)
        return context


class WarningHealthCheckView(CustomHealthCheckView):
    """
    Display non critical healthcheck errors.
    """

    title: str = "System warnings"

    @property
    def plugins(self):
        return [p for p in super().plugins if p.critical_service and not p.status]


def pingdom_healthcheck(request):
    status_code = 503
    context = {"status": "FALSE"}
    check_mixin = CheckMixin()

    errors = check_mixin.check()
    if not errors:
        status_code = 200
        context["status"] = "OK"

    return TemplateResponse(
        request,
        template="core_health_check/pingdom.html",
        context=context,
        content_type="text/xml",
        status=status_code,
    )
