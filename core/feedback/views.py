from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import FormView

from core.feedback.forms import BetaFeedbackForm


class BetaFeedbackView(FormView):
    template_name = "feedback/beta_feedback.html"
    form_class = BetaFeedbackForm
    success_url = reverse_lazy("feedback-thank-you")

    def get_initial(self):
        initial = super().get_initial()
        initial["submitter"] = self.request.user
        return initial

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


def feedback_thank_you(request):
    return render(request, "feedback/thank_you.html")
