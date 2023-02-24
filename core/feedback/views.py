from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView

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
    context_object_name = "feedbacks"

    def get_queryset(self):
        return BetaServiceFeedback.objects.all().order_by("-pk")
