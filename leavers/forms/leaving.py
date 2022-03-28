from django import forms
from django.forms import RadioSelect

from core.forms import GovFormattedForm


class WhoIsLeavingForm(GovFormattedForm):
    CHOICES = [
        ("me", "Me"),
        ("someone_else", "Someone Else"),
    ]

    who_for = forms.ChoiceField(
        label="",
        choices=CHOICES,
        widget=RadioSelect,
    )
