from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.generic import FormView, ListView

from core import notify
from core.feedback.forms import BetaFeedbackForm
from core.feedback.models import BetaServiceFeedback


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
        # Send an email to inform the team of the feedback
        notify.email(
            email_addresses=[settings.JML_TEAM_CONTACT_EMAIL],
            template_id=notify.EmailTemplates.FEEDBACK_NOTIFICATION_EMAIL,
            personalisation={
                "feedback_url": settings.SITE_URL + reverse("feedback-listing"),
            },
        )
        return super().form_valid(form)


def feedback_thank_you(request):
    return render(request, "feedback/thank_you.html")


class UserCanViewFeedback(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.has_perm("feedback.view_betaservicefeedback")


class FeedbackListingView(UserCanViewFeedback, ListView):
    template_name = "feedback/feedback_listing.html"
    model = BetaServiceFeedback
    paginate_by = 25

    def get_queryset(self):
        return BetaServiceFeedback.objects.all().order_by("-submitted_at")
