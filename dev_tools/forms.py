from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Field, Layout, Submit
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()


def get_user_choices():
    return [
        (None, "AnonymousUser"),
        *[(x.id, f"{str(x)} ({x.groups.first()})") for x in User.objects.all()],
    ]


class ChangeUserForm(forms.Form):
    user = forms.ChoiceField(
        label="Choose a user to impersonate",
        choices=get_user_choices,
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("user"),
            Submit("submit", "Select user"),
        )


class CreateUserForm(forms.Form):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    group = forms.ModelChoiceField(
        label="Group",
        queryset=Group.objects.all(),
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("first_name"),
            Field("last_name"),
            Field("email"),
            Field("group"),
            Submit("submit", "Create user"),
        )

    def clean_email(self):
        """
        Check if the email is already in use.
        """
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(f"{email} is already in use.")
        return email
