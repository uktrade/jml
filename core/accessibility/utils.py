from core.accessibility.models import AccessibilityStatement


def get_accessibility_statement() -> AccessibilityStatement | None:
    return AccessibilityStatement.objects.last()
