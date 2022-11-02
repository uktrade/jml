from functools import wraps

from django.shortcuts import redirect
from django.urls import reverse

from activity_stream.models import ActivityStreamStaffSSOUser
from core.people_data import get_people_data_interface
from user.models import User


def leaver_does_not_have_duplicate_person_ids():
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            SESSION_KEY = "duplicate_person_ids_passed"
            person_id_error_page = reverse("leaver-duplicate-person-ids-error")

            # The user has already been checked and verified.
            if SESSION_KEY in request.session:
                print("Session key found")
                print(request.session[SESSION_KEY])
                if request.session[SESSION_KEY]:
                    return view_func(request, *args, **kwargs)
                else:
                    return redirect(person_id_error_page)

            user: User = request.user

            # If we can't get an ActivityStreamStaffSSOUser, then the user
            # can't use our service.
            activitystream_user = ActivityStreamStaffSSOUser.objects.get(
                email_user_id=user.sso_email_user_id,
            )

            user_emails = activitystream_user.sso_emails.all().values_list(
                "email_address", flat=True
            )
            print(user_emails)

            people_data_interface = get_people_data_interface()
            multiple_person_id_emails = (
                people_data_interface.get_emails_with_multiple_person_ids()
            )

            # Check if any of the user's emails are a known multiple Person ID email.
            if any(email in multiple_person_id_emails for email in user_emails):
                request.session[SESSION_KEY] = False
                request.session.save()
                return redirect(person_id_error_page)

            request.session[SESSION_KEY] = True
            request.session.save()
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
