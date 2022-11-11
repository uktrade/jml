from django.template.response import TemplateResponse


def contact_us_page(request):
    context = {
        "page_title": "Contact us",
    }
    return TemplateResponse(request, "landing_pages/contact_us_page.html", context)


def leaver_landing_page(request):
    context = {
        "page_title": "Leavers and Line Managers",
    }
    return TemplateResponse(request, "landing_pages/leaver_landing_page.html", context)


def data_processor_landing_page(request):
    context = {
        "page_title": "Data Processors",
    }
    return TemplateResponse(
        request, "landing_pages/data_processor_landing_page.html", context
    )
