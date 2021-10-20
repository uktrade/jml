from django.views.generic import TemplateView


class LeaversStartView(TemplateView):
    template_name = "leaving_details/start.html"


class LeaverOrLineManagerView(TemplateView):
    template_name = "leaving_details/leaver_or_line_manager.html"


class LeavingDetailsView(TemplateView):
    template_name = "leaving_details/details.html"


class PersonalInfoView(TemplateView):
    template_name = "leaving_details/personal.html"


class ProfessionalInfoView(TemplateView):
    template_name = "leaving_details/professional.html"


# TODO - kit and service access?


class ConfirmationSummaryView(TemplateView):
    template_name = "leaving_details/confirmation.html"
