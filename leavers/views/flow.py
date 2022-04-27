from django.contrib.auth.mixins import UserPassesTestMixin
from django_workflow_engine.views import (
    FlowContinueView,
    FlowCreateView,
    FlowListView,
    FlowView,
)


class LeaverBaseView(UserPassesTestMixin):
    page_title: str = "Leaving Flow"

    def test_func(self):
        return self.request.user.groups.filter(
            name__in=(
                "SRE",
                "Security Team",
            ),
        ).first()

    def get_page_title(self) -> str:
        return self.page_title

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.get_page_title()
        return context


class LeaversFlowListView(
    LeaverBaseView,
    FlowListView,
):
    template_name = "flow/flow_list.html"
    page_title = "Leaving Requests"


class LeaversFlowCreateView(
    LeaverBaseView,
    FlowCreateView,
):
    template_name = "flow/flow_form.html"
    page_title = "Create Leaving Request"


class LeaversFlowContinueView(
    LeaverBaseView,
    FlowContinueView,
):
    template_name = "flow/flow_continue.html"
    page_title = "Continue Leaving Request"


class LeaversFlowView(
    LeaverBaseView,
    FlowView,
):
    template_name = "flow/flow_detail.html"
    page_title = "Leaving Request"

    def get_page_title(self) -> str:
        return f"{self.object.workflow_name} - {self.object.flow_name}"
