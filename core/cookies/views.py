from typing import Literal

from django.http.request import HttpRequest
from django.shortcuts import redirect
from django.template.response import TemplateResponse


def cookie_notice(request):
    return TemplateResponse(request, "cookies/notice.html", {})


def cookie_response(request: HttpRequest, response: Literal["accept", "reject"]):
    redirect_response = redirect(request.GET.get("next", "/"))
    redirect_response.set_cookie(
        "cookie_banner_response",
        response,
        max_age=31536000,  # 1 year
    )
    return redirect_response
