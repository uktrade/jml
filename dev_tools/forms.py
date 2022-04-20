from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from core.forms import GovFormattedForm

User = get_user_model()


def get_user_choices():
    return [
        (None, "AnonymousUser"),
        *[(x.id, f"{str(x)} ({x.groups.first()})") for x in User.objects.all()],
    ]


class ChangeUserForm(GovFormattedForm):
    user = forms.ChoiceField(
        label="Choose a user to impersonate",
        choices=get_user_choices,
        required=True,
    )


class CreateUserForm(GovFormattedForm):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    group = forms.ModelChoiceField(
        label="Group",
        queryset=Group.objects.all(),
        required=True,
    )

    def clean_email(self):
        """
        Check if the email is already in use.
        """
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(f"{email} is already in use.")
        return email
