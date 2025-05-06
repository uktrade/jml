from typing import Literal, Optional

from django.http.request import HttpRequest
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.http import url_has_allowed_host_and_scheme

COOKIE_KEY = "cookies_policy"


def cookie_notice(request):
    context = {}
    context.update(page_title="Cookie Notice")
    return TemplateResponse(request, "cookies/notice.html", context)


def cookie_response(request: HttpRequest, response: Literal["accept", "reject"]):
    cookie_value_mapping = {
        "accept": "true",
        "reject": "false",
    }
    cookie_value = cookie_value_mapping[response]

    next_path: Optional[str] = request.GET.get("next")
    if (
        not url_has_allowed_host_and_scheme(next_path, allowed_hosts=None)
        or not next_path
    ):
        next_path = "/"

    redirect_response = redirect(next_path)
    redirect_response.set_cookie(
        COOKIE_KEY,
        cookie_value,
        max_age=31536000,  # 1 year
    )
    return redirect_response
