from django.shortcuts import (
    redirect,
    render,
    reverse,
)

from django_workflow_engine.views import (
    FlowListView,
    FlowCreateView,
    FlowContinueView,
    FlowView,
)

from leavers.forms import LeaversForm
from leavers.models import LeavingRequest


def leaving_requests(request):
    context = {'leaving_requests': LeavingRequest.objects.all()}
    return render(request, "leaving_requests.html", context)


def leavers_form(request):
    if request.method == 'POST':
        form = LeaversForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect(reverse('leaving_requests'))
    else:
        form = LeaversForm()

    context = {
        'form': form,
    }

    return render(request, 'leaver_form.html', context)


class LeaversFlowListView(FlowListView):
    template_name = "flow_list.html"


class LeaversFlowCreateView(FlowCreateView):
    template_name = "flow_form.html"


class LeaversFlowContinueView(FlowContinueView):
    # TODO: Can't override template like this for the continue view.
    template_name = "flow_continue.html"


class LeaversFlowView(FlowView):
    template_name = "flow_detail.html"
