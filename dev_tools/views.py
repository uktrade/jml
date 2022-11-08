from functools import wraps

from dev_tools import utils
from dev_tools.forms import ChangeUserForm, CreateUserForm
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import SuspiciousOperation
from django.shortcuts import redirect, render
from django.urls import reverse

User = get_user_model()

DEV_TOOLS_ENABLED = settings.DEV_TOOLS_ENABLED


def dev_tools_context(request):
    return {
        "DEV_TOOLS_ENABLED": DEV_TOOLS_ENABLED,
    }


def check_dev_tools_enabled(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not DEV_TOOLS_ENABLED:
            raise SuspiciousOperation("Dev tools are not enabled")

        return func(*args, **kwargs)

    return wrapper


@check_dev_tools_enabled
def index(request):
    context = {
        "change_user_form": ChangeUserForm(initial={"user": request.user.pk}),
        "create_user_form": CreateUserForm(),
    }

    return render(request, "dev_tools/index.html", context=context)


@check_dev_tools_enabled
def create_user(request):
    context = {
        "change_user_form": ChangeUserForm(initial={"user": request.user.pk}),
        "create_user_form": CreateUserForm(),
    }

    form = CreateUserForm(data=request.POST)

    if not form.is_valid():
        context.update(create_user_form=form)
        return render(request, "dev_tools/index.html", context=context)

    form_data = form.cleaned_data

    user, _, _ = utils.create_user(
        first_name=form_data["first_name"],
        last_name=form_data["last_name"],
        email=form_data["email"],
        group=form_data["group"],
    )

    utils.change_user(request=request, user_pk=user.pk)

    return redirect(reverse("dev_tools:index"))


@check_dev_tools_enabled
def change_user(request):
    context = {
        "change_user_form": ChangeUserForm(initial={"user": request.user.pk}),
        "create_user_form": CreateUserForm(),
    }

    form = ChangeUserForm(data=request.POST)

    if not form.is_valid():
        context.update(change_user_form=form)
        return render(request, "dev_tools/index.html", context=context)

    utils.change_user(request=request, user_pk=form.cleaned_data["user"])

    return redirect(reverse("dev_tools:index"))
