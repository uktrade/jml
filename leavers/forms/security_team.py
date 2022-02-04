from typing import Dict

from django import forms

from core.forms import GovFormattedForm


class SecurityTeamConfirmCompleteForm(GovFormattedForm):
    building_pass_access_revoked = forms.BooleanField(
        label="Building Pass Access Revoked",
        required=True,
    )
    rosa_access_revoked = forms.BooleanField(
        label="ROSA Access Revoked (where appropriate)",
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        required_message_replacement: Dict[str, str] = {
            "building_pass_access_revoked": "Building Pass Access Revoked",
            "rosa_access_revoked": "ROSA Access Revoked",
        }
        for field_name, field in self.fields.items():
            if field_name in required_message_replacement:
                message_replacement = required_message_replacement[field_name]
                field.error_messages[
                    "required"
                ] = f"Select {message_replacement} to confirm removal."
