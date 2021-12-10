from django.views.generic import TemplateView
from django.urls import reverse_lazy
from django.shortcuts import reverse
from django.views.generic.edit import FormView


from leavers.forms import (
    WhoIsLeavingForm,
)


class CannotFindLeaverException(Exception):
    pass


class LeaversStartView(TemplateView):
    template_name = "leaving/start.html"


class WhoIsLeavingView(FormView):
    template_name = "leaving/who_is_leaving.html"
    form_class = WhoIsLeavingForm
    success_url = reverse_lazy("search")

    def form_valid(self, form):
        self.who_for = form.cleaned_data["who_for"]
        return super().form_valid(form)

    def get_success_url(self):
        if self.who_for == "me":
            return reverse("leaver-confirm-details")
        else:
            return reverse("line-manager-search")
