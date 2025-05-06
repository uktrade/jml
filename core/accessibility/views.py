from django.template.response import TemplateResponse

from core.accessibility.utils import get_accessibility_statement


def accessibility_statement(request):
    context = {
        "page_title": "Accessibility statement",
        "accessibility_statement": get_accessibility_statement(),
    }
    return TemplateResponse(request, "accessibility/statement.html", context)
