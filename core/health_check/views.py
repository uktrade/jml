from typing import Any, Dict

from django.http import HttpResponse, JsonResponse

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
    title: str = "System warnings"

    @property
    def plugins(self):
        return [p for p in super().plugins if p.critical_service and not p.status]
