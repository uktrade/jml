from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    UserPassesTestMixin,
)
from django_workflow_engine.views import (
    FlowListView,
    FlowCreateView,
    FlowContinueView,
    FlowView,
)


class LeaverBaseView(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.groups.filter(
            name__in=(
                "SRE",
                "HR",
            ),
        ).first()


class LeaversFlowListView(
    LoginRequiredMixin,
    LeaverBaseView,
    FlowListView,
):
    template_name = "flow/flow_list.html"


class LeaversFlowCreateView(
    LoginRequiredMixin,
    LeaverBaseView,
    FlowCreateView,
):
    template_name = "flow/flow_form.html"


class LeaversFlowContinueView(
    LoginRequiredMixin,
    LeaverBaseView,
    FlowContinueView,
):
    # TODO: Can't override template like this for the continue view.
    template_name = "flow/flow_continue.html"


class LeaversFlowView(
    LoginRequiredMixin,
    LeaverBaseView,
    FlowView,
):
    template_name = "flow/flow_detail.html"
