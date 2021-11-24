from typing import Optional

from django.http.request import HttpRequest

from core.staff_sso import get_staff_sso_interface
from core.staff_sso.interfaces import SSOUserDetail


def get_sso_user_details(
    *, request: HttpRequest, email: str
) -> Optional[SSOUserDetail]:
    """
    Get user details from Staff SSO for a given email address
    """
    interface = get_staff_sso_interface(request=request)
    return interface.get_user_details(email=email)
