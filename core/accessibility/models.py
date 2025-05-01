from django.db import models
from django_prose_editor.fields import ProseEditorField


class AccessibilityStatement(models.Model):
    content = ProseEditorField(
        extensions={
            "Bold": True,
            "Italic": True,
            "BulletList": True,
            "Link": True,
            "Table": True,
            "Heading": {"levels": [2, 3]},
        },
        sanitize=True,
    )
