from django.views.generic import TemplateView
from django.urls import reverse_lazy
from django.views.generic.edit import FormView

from leavers.forms import WhoIsLeavingForm, WhenAreTheyLeavingForm


class LeaversStartView(TemplateView):
    template_name = "leaving_details/start.html"


class LeaverOrLineManagerView(TemplateView):
    template_name = "leaving_details/leaver_or_line_manager.html"


class LeavingSearchView(TemplateView):
    template_name = "leaving_details/search.html"


class LeavingDetailsView(FormView):
    template_name = "leaving_details/details.html"
    form_class = WhoIsLeavingForm
    success_url = reverse_lazy("search")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['who_is_leaving_form'] = self.form_class
        context['when_are_they_leaving_form'] = WhenAreTheyLeavingForm()
        return context


class LeavingSearchResultView(TemplateView):
    template_name = "leaving_details/search-result.html"


class LeavingSaveView(TemplateView):
    template_name = "leaving_details/saved.html"


class PersonalInfoView(TemplateView):
    template_name = "leaving_details/personal.html"


class ProfessionalInfoView(TemplateView):
    template_name = "leaving_details/professional.html"


# TODO - kit and service access?


class ConfirmationSummaryView(TemplateView):
    template_name = "leaving_details/confirmation.html"
