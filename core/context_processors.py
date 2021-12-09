def cookies_context(request):
    return {
        "COOKIE_RESPONSE": request.COOKIES.get("cookie_banner_response"),
    }
