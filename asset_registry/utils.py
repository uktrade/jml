from typing import Optional, Tuple

from django.http import HttpRequest

ADD_USER_SUCCESS_SESSION_KEY = "add_user_success"
ADD_USER_ERROR_SESSION_KEY = "add_user_error"
REMOVE_USER_SUCCESS_SESSION_KEY = "remove_user_success"


def get_asset_user_action_messages(
    request: HttpRequest,
) -> Tuple[Optional[str], Optional[str]]:
    success_message: Optional[str] = None
    add_user_success: Optional[str] = request.session.get(ADD_USER_SUCCESS_SESSION_KEY)
    remove_user_success: Optional[str] = request.session.get(
        REMOVE_USER_SUCCESS_SESSION_KEY
    )
    if add_user_success or remove_user_success:
        success_message = add_user_success or remove_user_success

    error_message: Optional[str] = None
    add_user_error: Optional[str] = request.session.get(ADD_USER_ERROR_SESSION_KEY)
    if remove_user_success:
        error_message = add_user_error

    # Clean up the session
    if ADD_USER_SUCCESS_SESSION_KEY in request.session:
        del request.session[ADD_USER_SUCCESS_SESSION_KEY]
    if ADD_USER_ERROR_SESSION_KEY in request.session:
        del request.session[ADD_USER_ERROR_SESSION_KEY]
    if REMOVE_USER_SUCCESS_SESSION_KEY in request.session:
        del request.session[REMOVE_USER_SUCCESS_SESSION_KEY]

    return success_message, error_message
