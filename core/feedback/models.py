from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.enums import TextChoices


class SatisfactionOptions(TextChoices):
    """
    Enum for the satisfaction options.
    """

    VERY_DISSATISFIED = "very_dissatisfied", "Very dissatisfied"
    DISSATISFIED = "dissatisfied", "Dissatisfied"
    NEUTRAL = "neutral", "Neither satisfied or dissatisfied"
    SATISFIED = "satisfied", "Satisfied"
    VERY_SATISFIED = "very_satisfied", "Very satisfied"


class BetaServiceFeedback(models.Model):
    satisfaction = models.CharField(max_length=30, choices=SatisfactionOptions.choices)
    comment = models.TextField(blank=True)
    submitter = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Beta Feedback Submission"
        verbose_name_plural = "Beta Feedback Submissions"
