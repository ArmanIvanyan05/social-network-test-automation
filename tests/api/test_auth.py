"""Authentication API contract and security tests."""

import pytest

from social_network_automation.api.domain import AuthClient
from social_network_automation.api.models import AuthSession, User
from social_network_automation.assertions import assert_error, assert_no_password_data
from social_network_automation.cleanup import ResourceTracker
from social_network_automation.data import RegistrationData, UserDataFactory

pytestmark = [pytest.mark.api, pytest.mark.auth, pytest.mark.regression]


def register(
    auth: AuthClient, factory: UserDataFactory, tracker: ResourceTracker
) -> tuple[RegistrationData, AuthSession]:
    """Create a tracked user for one test."""
    data = factory.registration()
    response = auth.register(data)
    assert response.status_code == 201
    session = AuthSession.model_validate(response.json())
    return data, tracker.track(session)


@pytest.mark.smoke
def test_successful_registration(
    auth_client: AuthClient, user_data_factory: UserDataFactory, resource_tracker: ResourceTracker
) -> None:
    data, session = register(auth_client, user_data_factory, resource_tracker)
    assert session.user.username == data.username
    assert session.user.email == data.email
    assert session.token


def test_duplicate_registration(
    auth_client: AuthClient, user_data_factory: UserDataFactory, resource_tracker: ResourceTracker
) -> None:
    data, _ = register(auth_client, user_data_factory, resource_tracker)
    assert_error(auth_client.register(data), 409, "DUPLICATE_USER")


def test_registration_rejects_missing_fields(auth_client: AuthClient) -> None:
    error = assert_error(
        auth_client.register({"email": "missing@example.test"}), 400, "VALIDATION_ERROR"
    )
    assert error.message == "Required fields are missing"


def test_registration_rejects_invalid_email(auth_client: AuthClient) -> None:
    assert_error(
        auth_client.register({"username": "valid", "email": "invalid", "password": "valid"}),
        400,
        "VALIDATION_ERROR",
    )


@pytest.mark.smoke
def test_successful_login(
    auth_client: AuthClient, user_data_factory: UserDataFactory, resource_tracker: ResourceTracker
) -> None:
    data, registered = register(auth_client, user_data_factory, resource_tracker)
    response = auth_client.login(data.email, data.password)
    assert response.status_code == 200
    logged_in = AuthSession.model_validate(response.json())
    assert logged_in.user.id == registered.user.id
    assert logged_in.token


def test_login_rejects_incorrect_password(
    auth_client: AuthClient, user_data_factory: UserDataFactory, resource_tracker: ResourceTracker
) -> None:
    data, _ = register(auth_client, user_data_factory, resource_tracker)
    assert_error(auth_client.login(data.email, "incorrect-password"), 401, "INVALID_CREDENTIALS")


def test_login_rejects_unknown_email(auth_client: AuthClient) -> None:
    assert_error(
        auth_client.login("unknown-automation@example.test", "irrelevant"),
        401,
        "INVALID_CREDENTIALS",
    )


def test_login_rejects_missing_fields(auth_client: AuthClient) -> None:
    response = auth_client.login_payload({"email": "only@example.test"})
    assert_error(response, 400, "VALIDATION_ERROR")


def test_current_user_accepts_valid_bearer_token(
    auth_client: AuthClient, registered_user: tuple[RegistrationData, AuthSession]
) -> None:
    _, session = registered_user
    response = auth_client.current_user(token=session.token)
    assert response.status_code == 200
    assert User.model_validate(response.json()["user"]).id == session.user.id


def test_current_user_rejects_missing_token(auth_client: AuthClient) -> None:
    assert_error(auth_client.current_user(), 401, "MISSING_TOKEN")


def test_current_user_rejects_malformed_header(auth_client: AuthClient) -> None:
    assert_error(auth_client.current_user(authorization="not-bearer"), 401, "MALFORMED_AUTH_HEADER")


def test_current_user_rejects_invalid_token(auth_client: AuthClient) -> None:
    assert_error(auth_client.current_user(token="invalid-token"), 401, "INVALID_TOKEN")


def test_profile_rejects_malformed_user_id(auth_client: AuthClient) -> None:
    assert_error(auth_client.profile("not-an-object-id"), 400, "INVALID_USER_ID")


def test_authentication_responses_never_expose_passwords(
    auth_client: AuthClient, user_data_factory: UserDataFactory, resource_tracker: ResourceTracker
) -> None:
    data = user_data_factory.registration()
    registration = auth_client.register(data)
    session = resource_tracker.track(AuthSession.model_validate(registration.json()))
    login = auth_client.login(data.email, data.password)
    current = auth_client.current_user(token=session.token)
    profile = auth_client.profile(session.user.id)
    for response in (registration, login, current, profile):
        assert_no_password_data(response.json())


def test_complete_registration_login_current_user_flow(
    auth_client: AuthClient, user_data_factory: UserDataFactory, resource_tracker: ResourceTracker
) -> None:
    data, registered = register(auth_client, user_data_factory, resource_tracker)
    login = AuthSession.model_validate(auth_client.login(data.email, data.password).json())
    current = User.model_validate(auth_client.current_user(token=login.token).json()["user"])
    assert registered.user.id == login.user.id == current.id
