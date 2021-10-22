from django.views.generic import TemplateView

from django.views.generic.edit import FormView

from django.core.exceptions import ValidationError

from leavers.forms import DetailsForm


class LeaversStartView(TemplateView):
    template_name = "leaving_details/start.html"


class LeaverOrLineManagerView(TemplateView):
    template_name = "leaving_details/leaver_or_line_manager.html"

class LeavingSearchView(TemplateView):
    template_name = "leaving_details/search.html"

# class LeavingDetailsView(DetailsForm):
#     template_name = "leaving_details/details.html"


class LeavingDetailsView(FormView):
    template_name = "leaving_details/details.html"
    form_class = DetailsForm
    success_url = '/start/'

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        if form.is_valid():
            self.flow.leaving_request.last_day = form.cleaned_data["last_day"]
            if form.cleaned_data["for_self"]:
                self.flow.leaving_request.leaver_user = self.user
            else:
                self.flow.leaving_request.requester_user = self.user
            self.flow.leaving_request.save()
        else:
            raise ValidationError("Form is not valid", {"form": form})

        return None, form.cleaned_data

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
