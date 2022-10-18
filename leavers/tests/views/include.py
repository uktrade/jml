from typing import Any, Dict, List

from django.conf import settings
from django.urls import reverse

from user.test.factories import UserFactory


class ViewAccessTest:
    """
    Tests to make sure unauthenticated users can't access the view
    and to make sure only the required methods are accessible to logged in users.
    """

    view_name: str = ""
    view_kwargs: Dict[str, Any] = {}
    allowed_methods: List[str] = ["get", "post", "patch", "put"]
    url_query_params: str = ""

    def get_url(self) -> str:
        view_path = reverse(
            viewname=self.view_name,
            **self.view_kwargs,  # type: ignore
        )
        if self.url_query_params:
            return f"{view_path}?{self.url_query_params}"
        return view_path

    def setUp(self):
        self.authenticated_user = UserFactory()

    """
    Unauthenticated user checks
    """

    def assert_unauthenticated_pass(self, response):
        self.assertEqual(response.status_code, 302)
        self.assertTrue(str(settings.LOGIN_URL) in response.url)

    def test_unauthenticated_user_get(self, *args, **kwargs):
        response = self.client.get(self.get_url())
        self.assert_unauthenticated_pass(response)

    def test_unauthenticated_user_post(self, *args, **kwargs):
        response = self.client.post(self.get_url(), {})
        self.assert_unauthenticated_pass(response)

    def test_unauthenticated_user_patch(self, *args, **kwargs):
        response = self.client.patch(self.get_url(), {})
        self.assert_unauthenticated_pass(response)

    def test_unauthenticated_user_put(self, *args, **kwargs):
        response = self.client.put(self.get_url(), {})
        self.assert_unauthenticated_pass(response)

    """
    Authenticated user checks
    """

    def assert_authenticated_pass(self, method: str, response):
        status_code = 200 if method in self.allowed_methods else 405
        self.assertEqual(response.status_code, status_code)  # type: ignore

    def test_authenticated_user_get(self, *args, **kwargs):
        self.client.force_login(self.authenticated_user)
        response = self.client.get(self.get_url())
        self.assert_authenticated_pass("get", response)

    def test_authenticated_user_post(self, *args, **kwargs):
        self.client.force_login(self.authenticated_user)
        response = self.client.post(self.get_url(), {})
        self.assert_authenticated_pass("post", response)

    def test_authenticated_user_patch(self, *args, **kwargs):
        self.client.force_login(self.authenticated_user)
        response = self.client.patch(self.get_url(), {})
        self.assert_authenticated_pass("patch", response)

    def test_authenticated_user_put(self, *args, **kwargs):
        self.client.force_login(self.authenticated_user)
        response = self.client.put(self.get_url(), {})
        self.assert_authenticated_pass("put", response)
