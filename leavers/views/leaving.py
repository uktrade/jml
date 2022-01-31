from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from leavers.forms import leaving as Leaving_form


class CannotFindLeaverException(Exception):
    pass


class LeaversStartView(TemplateView):
    template_name = "leaving/start.html"


class WhoIsLeavingView(FormView):
    template_name = "leaving/who_is_leaving.html"
    form_class = Leaving_form.WhoIsLeavingForm
    success_url = reverse_lazy("report-a-leaver-search")

    def form_valid(self, form):
        self.who_for = form.cleaned_data["who_for"]
        return super().form_valid(form)

    def get_success_url(self):
        if self.who_for == "me":
            return reverse("leaver-update-details")
        else:
            return reverse("report-a-leaver-search")
