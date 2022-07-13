from django.conf import settings
from django.template.response import TemplateResponse


def leaver_landing_page(request):
    context = {}
    context.update(
        page_title="Leavers and Line Managers",
        JML_TEAM_CONTACT_EMAIL=settings.JML_TEAM_CONTACT_EMAIL,
    )
    return TemplateResponse(request, "landing_pages/leaver_landing_page.html", context)


def data_processor_landing_page(request):
    context = {}
    context.update(
        page_title="Data Processors",
        JML_TEAM_CONTACT_EMAIL=settings.JML_TEAM_CONTACT_EMAIL,
    )
    return TemplateResponse(
        request, "landing_pages/data_processor_landing_page.html", context
    )
