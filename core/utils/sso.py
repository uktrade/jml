from typing import Optional

from core.staff_sso import get_staff_sso_interface
from core.staff_sso.interfaces import SSOUserDetail


def get_sso_user_details(*, email: str) -> Optional[SSOUserDetail]:
    """
    Get user details from Staff SSO for a given email address
    """
    interface = get_staff_sso_interface()
    print("CAM WAS HERE")
    print(interface)
    print(interface.get_user_details(email=email))
    return interface.get_user_details(email=email)
