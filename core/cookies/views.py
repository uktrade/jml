from typing import Literal

from django.http.request import HttpRequest
from django.shortcuts import redirect
from django.template.response import TemplateResponse

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

    redirect_response = redirect(request.GET.get("next", "/"))
    redirect_response.set_cookie(
        COOKIE_KEY,
        cookie_value,
        max_age=31536000,  # 1 year
    )
    return redirect_response
