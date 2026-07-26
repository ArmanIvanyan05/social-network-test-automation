"""Browser authentication coverage using accessible selectors."""

import pytest
from playwright.sync_api import Page, expect

from social_network_automation.api.domain import AuthClient
from social_network_automation.api.models import AuthSession
from social_network_automation.cleanup import ResourceTracker
from social_network_automation.config import Settings
from social_network_automation.data import RegistrationData, UserDataFactory
from social_network_automation.ui import LoginPage, PostsPage, SignupPage

pytestmark = [pytest.mark.ui, pytest.mark.auth, pytest.mark.regression]


def track_ui_user(page: Page, auth: AuthClient, tracker: ResourceTracker) -> AuthSession:
    """Track the user represented by the browser token."""
    token = PostsPage(page, "").token()
    assert token is not None
    response = auth.current_user(token=token)
    session = AuthSession(token=token, user=response.json()["user"])
    return tracker.track(session)


@pytest.mark.smoke
def test_successful_registration(
    page: Page,
    settings: Settings,
    user_data_factory: UserDataFactory,
    auth_client: AuthClient,
    resource_tracker: ResourceTracker,
) -> None:
    data = user_data_factory.registration()
    signup = SignupPage(page, settings.frontend_base_url)
    signup.open()
    signup.register(data.username, data.email, data.password)
    expect(page.get_by_role("heading", name="Posts")).to_be_visible()
    track_ui_user(page, auth_client, resource_tracker)


@pytest.mark.smoke
def test_successful_login(
    page: Page,
    settings: Settings,
    registered_user: tuple[RegistrationData, AuthSession],
) -> None:
    data, _ = registered_user
    login = LoginPage(page, settings.frontend_base_url)
    login.open()
    login.login(data.email, data.password)
    expect(page.get_by_role("heading", name="Posts")).to_be_visible()


def test_incorrect_credentials_show_error(page: Page, settings: Settings) -> None:
    login = LoginPage(page, settings.frontend_base_url)
    login.open()
    login.login("unknown-ui@example.test", "wrong")
    expect(page.get_by_role("alert")).to_have_text("Invalid email or password")


def test_session_restores_after_reload(
    page: Page,
    settings: Settings,
    registered_user: tuple[RegistrationData, AuthSession],
) -> None:
    data, _ = registered_user
    login = LoginPage(page, settings.frontend_base_url)
    login.open()
    login.login(data.email, data.password)
    expect(page.get_by_role("heading", name="Posts")).to_be_visible()
    page.reload(wait_until="domcontentloaded")
    expect(page.get_by_text(f"Signed in as {data.username}")).to_be_visible()


def test_logout_clears_session(
    page: Page,
    settings: Settings,
    registered_user: tuple[RegistrationData, AuthSession],
) -> None:
    data, _ = registered_user
    login = LoginPage(page, settings.frontend_base_url)
    login.open()
    login.login(data.email, data.password)
    PostsPage(page, settings.frontend_base_url).logout()
    expect(page.get_by_role("heading", name="Log in")).to_be_visible()
    assert PostsPage(page, "").token() is None


def test_logged_out_user_cannot_access_protected_page(page: Page, settings: Settings) -> None:
    PostsPage(page, settings.frontend_base_url).open()
    expect(page.get_by_role("heading", name="Log in")).to_be_visible()


def test_authenticated_user_is_redirected_from_public_pages(
    page: Page,
    settings: Settings,
    registered_user: tuple[RegistrationData, AuthSession],
) -> None:
    data, _ = registered_user
    login = LoginPage(page, settings.frontend_base_url)
    login.open()
    login.login(data.email, data.password)
    expect(page.get_by_role("heading", name="Posts")).to_be_visible()
    page.goto(f"{settings.frontend_base_url}/login")
    expect(page.get_by_role("heading", name="Posts")).to_be_visible()
    page.goto(settings.frontend_base_url)
    expect(page.get_by_role("heading", name="Posts")).to_be_visible()


def test_auth_forms_show_required_field_validation(page: Page, settings: Settings) -> None:
    signup = SignupPage(page, settings.frontend_base_url)
    signup.open()
    signup.submit_empty()
    expect(page.get_by_text("Username is required")).to_be_visible()
    expect(page.get_by_text("Email is required")).to_be_visible()
    expect(page.get_by_text("Password is required")).to_be_visible()
    login = LoginPage(page, settings.frontend_base_url)
    login.open()
    login.submit_empty()
    expect(page.get_by_text("Email is required")).to_be_visible()
    expect(page.get_by_text("Password is required")).to_be_visible()
