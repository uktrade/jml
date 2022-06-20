from enum import Enum
from typing import Optional

from django.http.request import HttpRequest


class SecuritySubRole(Enum):
    BUILDING_PASS = "bp"
    ROSA_KIT = "rk"


def set_security_role(request: HttpRequest, role: SecuritySubRole):
    """
    Set the security role to the Session.
    """

    request.session["security_role"] = role.value
    request.session.save()


def get_security_role(request: HttpRequest) -> SecuritySubRole:
    """
    Get the security role from the URL or Session.

    If there is no role set yet, default to the Building Pass role.
    """

    role_value: Optional[str] = request.session.get("security_role", None)
    url_value: Optional[str] = request.GET.get("security-role")
    if url_value:
        role_value = url_value

    role: SecuritySubRole = SecuritySubRole.BUILDING_PASS
    if role_value:
        try:
            role = SecuritySubRole(role_value)
        except ValueError:
            pass
        set_security_role(request, role)

    return role
