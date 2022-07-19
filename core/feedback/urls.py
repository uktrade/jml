from django.urls import path

from core.feedback import views

urlpatterns = [
    path("", views.BetaFeedbackView.as_view(), name="beta-service-feedback"),
    path("thank-you/", views.feedback_thank_you, name="feedback-thank-you"),
]
