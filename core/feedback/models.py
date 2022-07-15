from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.enums import TextChoices


class SatisfactionOptions(TextChoices):
    """
    Enum for the satisfaction options.
    """

    VERY_SATISFIED = "very_satisfied", "Very satisfied"
    SATISFIED = "satisfied", "Satisfied"
    NEUTRAL = "neutral", "Neither satisfied or dissatisfied"
    DISSATISFIED = "dissatisfied", "Dissatisfied"
    VERY_DISSATISFIED = "very_dissatisfied", "Very dissatisfied"


class BetaServiceFeedback(models.Model):
    satisfaction = models.CharField(max_length=30, choices=SatisfactionOptions.choices)
    comment = models.TextField(blank=True)
    submitter = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
