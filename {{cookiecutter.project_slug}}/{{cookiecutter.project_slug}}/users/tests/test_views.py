import pytest
from django.conf import settings
from django.contrib import messages
from django.test import Client
from django.urls import reverse

from {{ cookiecutter.project_slug }}.users.forms import UserChangeForm
from {{ cookiecutter.project_slug }}.users.models import User

pytestmark = pytest.mark.django_db


class TestUserUpdateView:
    """
    Test class for all tests related to the User Update View
    """

    def dummy_get_response(self, request: HttpRequest):
        return None

    def test_get_success_url(
        self,
        user: User,
        client: Client,
    ):
        """
        Test to make sure the correct success url (User's detail view url)
        is returned for logged-in users
        """

        url = reverse("users:update")

        # Make User login
        client.force_login(user)

        response = client.post(path=url, data=self.form_data)

        # Make sure the correct url is returned with status_code 302
        # and the final constructed url page can be loaded with status_code 200
        assertRedirects(response, expected_url=f"/users/{user.username}/")

    def test_get_object(self, user: User, client: Client):
        """
        Test to make sure the correct User Model Instance
        is returned
        """
        url = reverse("users:update")

        # make client login
        client.force_login(user)

        response = client.get(path=url)

        assert response.context["view"].get_object() == user

    def test_form_valid(self, user: User, client: Client):
        """
        Test to make sure the correct success message is emitted for a valid form
        """

        url = reverse("users:update")

        # Make User login
        client.force_login(user)

        response = client.post(path=url, data=self.form_data)

        # Initialize the form
        form = UserChangeForm()
        form.cleaned_data = []
        view.form_valid(form)

        # assert correct success message is emmitted
        messages_sent = [
            (m.message, m.level_tag)
            for m in messages.get_messages(response.wsgi_request)
        ]
        assert messages_sent == [(_("Information successfully updated"), "success")]

class TestUserRedirectView:
    def test_get_redirect_url(self, user: User, client: Client):
        """
        Test to make sure authenticated (logged-in) users get redirected to their
        detail view page
        """
        url = reverse("users:redirect")
        
        # Make User login
        client.force_login(user)

        # Process request and get response
        response = client.get(path=url)

        # Make sure the correct url is returned with status_code 302
        # and the final constructed url page can be loaded with status_code 200
        assertRedirects(response, expected_url=f"/users/{user.username}/")


class TestUserDetailView:
    """
    Test class for all tests related to the User Detail View
    """

    def test_authenticated(self, user: User, client: Client):
        """
        Test to make sure authenticated (logged-in) users can checkout
        other users' detail view page
        """
        url = reverse("users:detail", kwargs={"username": user.username})

        # Make User login
        client.force_login(user)

        response = client.get(path=url)

        response = user_detail_view(request, username=user.username)

    def test_not_authenticated(self, user: User, client: Client):
        """
        Test to make sure unauthenticated users cannot checkout
        other users' detail view page and get successfully redirected to the login page url
        with the correct url to redirect user to thir detail page after they login
        """
        # Get Login Url
        login_url = reverse(settings.LOGIN_URL)

        url = reverse("users:detail", kwargs={"username": user.username})

        response = client.get(path=url)

        assert response.status_code == 302
        assert response.url == f"{login_url}?next=/fake-url/"
