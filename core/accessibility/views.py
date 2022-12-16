from django.template.response import TemplateResponse


def accessibility_statement(request):
    context = {
        "page_title": "Accessibility statement",
    }
    return TemplateResponse(request, "accessibility/statement.html", context)
