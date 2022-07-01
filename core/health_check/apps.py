from django.apps import AppConfig

from health_check.plugins import plugin_dir


class HealthCheckConfig(AppConfig):
    name = "core.health_check"
    label = "core_health_check"
    verbose_name = "Core health check"

    def ready(self):
        from core.health_check.backends import (  # PeopleFinderHealthCheck, TODO - reinstate
            ServiceNowHealthCheck,
        )

        plugin_dir.register(ServiceNowHealthCheck)
        # plugin_dir.register(PeopleFinderHealthCheck) TODO - reinstate
