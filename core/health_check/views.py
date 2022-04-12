from typing import Any, Dict

from django.http import HttpResponse, JsonResponse

from health_check.views import MainView


class CustomHealthCheckView(MainView):
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
