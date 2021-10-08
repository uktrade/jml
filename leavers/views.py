from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django_workflow_engine.views import (
    FlowListView,
    FlowCreateView,
    FlowContinueView,
    FlowView,
)


class LeaversFlowListView(FlowListView):
    template_name = "flow_list.html"


class LeaversFlowCreateView(FlowCreateView):
    template_name = "flow_form.html"


class LeaversFlowContinueView(
    FlowContinueView,
):
    # TODO: Can't override template like this for the continue view.
    template_name = "flow_continue.html"


class LeaversFlowView(
    FlowView,
):
    template_name = "flow_detail.html"
