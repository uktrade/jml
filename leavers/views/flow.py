from django.contrib.auth.mixins import UserPassesTestMixin
from django_workflow_engine.views import (
    FlowContinueView,
    FlowCreateView,
    FlowListView,
    FlowView,
)

# NOTE: These views don't have the LoginRequiredMixin because this is handled by
# the following MIDDLEWARE: /PS-IGNORE
# - dev_tools.middleware.DevToolsLoginRequiredMiddleware
# - authbroker_client.middleware.ProtectAllViewsMiddleware


class LeaverBaseView(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.groups.filter(
            name__in=(
                "SRE",
                "HR",
            ),
        ).first()


class LeaversFlowListView(
    LeaverBaseView,
    FlowListView,
):
    template_name = "flow/flow_list.html"


class LeaversFlowCreateView(
    LeaverBaseView,
    FlowCreateView,
):
    template_name = "flow/flow_form.html"


class LeaversFlowContinueView(
    LeaverBaseView,
    FlowContinueView,
):
    # TODO: Can't override template like this for the continue view.
    template_name = "flow/flow_continue.html"


class LeaversFlowView(
    LeaverBaseView,
    FlowView,
):
    template_name = "flow/flow_detail.html"
