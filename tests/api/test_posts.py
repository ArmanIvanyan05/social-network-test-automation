"""Posts API behavior and ownership tests."""

from uuid import uuid4

import pytest

from social_network_automation.api.domain import AuthClient, PostsClient
from social_network_automation.api.models import AuthSession, Post
from social_network_automation.assertions import assert_error, assert_no_password_data
from social_network_automation.cleanup import ResourceTracker
from social_network_automation.data import RegistrationData, UserDataFactory

pytestmark = [pytest.mark.api, pytest.mark.regression]


def create_post(posts: PostsClient, session: AuthSession, content: str | None = None) -> Post:
    """Create and parse one post."""
    response = posts.create(content or f"post-{uuid4().hex}", session.token)
    assert response.status_code == 201
    return Post.model_validate(response.json()["data"]["post"])


@pytest.mark.smoke
def test_create_text_post(
    posts_client: PostsClient, registered_user: tuple[RegistrationData, AuthSession]
) -> None:
    _, user = registered_user
    post = create_post(posts_client, user, "Portfolio post")
    assert post.content == "Portfolio post"
    assert post.author.id == user.user.id


def test_get_post_by_id(
    posts_client: PostsClient, registered_user: tuple[RegistrationData, AuthSession]
) -> None:
    _, user = registered_user
    created = create_post(posts_client, user)
    response = posts_client.get(created.id)
    assert response.status_code == 200
    assert Post.model_validate(response.json()["data"]["post"]).id == created.id


def test_list_users_posts(
    posts_client: PostsClient, registered_user: tuple[RegistrationData, AuthSession]
) -> None:
    _, user = registered_user
    created = create_post(posts_client, user)
    response = posts_client.list_for_user(user.user.id)
    posts = [Post.model_validate(item) for item in response.json()["data"]["posts"]]
    assert response.status_code == 200
    assert created.id in {post.id for post in posts}


def test_update_owned_post(
    posts_client: PostsClient, registered_user: tuple[RegistrationData, AuthSession]
) -> None:
    _, user = registered_user
    post = create_post(posts_client, user)
    response = posts_client.update(post.id, "Updated content", user.token)
    assert response.status_code == 200
    assert Post.model_validate(response.json()["data"]["post"]).content == "Updated content"


def test_delete_owned_post(
    posts_client: PostsClient, registered_user: tuple[RegistrationData, AuthSession]
) -> None:
    _, user = registered_user
    post = create_post(posts_client, user)
    assert posts_client.delete(post.id, user.token).status_code == 200
    assert_error(posts_client.get(post.id), 404, "POST_NOT_FOUND")


def test_reject_empty_post_content(
    posts_client: PostsClient, registered_user: tuple[RegistrationData, AuthSession]
) -> None:
    _, user = registered_user
    assert_error(posts_client.create("   ", user.token), 400, "VALIDATION_ERROR")


def test_reject_non_string_post_content(
    posts_client: PostsClient, registered_user: tuple[RegistrationData, AuthSession]
) -> None:
    _, user = registered_user
    assert_error(posts_client.create(42, user.token), 400, "VALIDATION_ERROR")


def test_post_creation_requires_authentication(posts_client: PostsClient) -> None:
    assert_error(posts_client.create("Protected"), 401, "MISSING_TOKEN")


def test_reject_malformed_post_id(posts_client: PostsClient) -> None:
    assert_error(posts_client.get("not-an-object-id"), 400, "INVALID_POST_ID")


def test_missing_post_returns_not_found(posts_client: PostsClient) -> None:
    assert_error(posts_client.get("507f1f77bcf86cd799439011"), 404, "POST_NOT_FOUND")


def test_other_user_cannot_update_post(
    posts_client: PostsClient,
    registered_user: tuple[RegistrationData, AuthSession],
    auth_client: AuthClient,
    user_data_factory: UserDataFactory,
    resource_tracker: ResourceTracker,
) -> None:
    _, owner = registered_user
    other_response = auth_client.register(user_data_factory.registration())
    other = resource_tracker.track(AuthSession.model_validate(other_response.json()))
    post = create_post(posts_client, owner)
    assert_error(posts_client.update(post.id, "stolen", other.token), 403, "POST_FORBIDDEN")


def test_other_user_cannot_delete_post(
    posts_client: PostsClient,
    registered_user: tuple[RegistrationData, AuthSession],
    auth_client: AuthClient,
    user_data_factory: UserDataFactory,
    resource_tracker: ResourceTracker,
) -> None:
    _, owner = registered_user
    other = resource_tracker.track(
        AuthSession.model_validate(auth_client.register(user_data_factory.registration()).json())
    )
    post = create_post(posts_client, owner)
    assert_error(posts_client.delete(post.id, other.token), 403, "POST_FORBIDDEN")


def test_post_responses_never_expose_passwords(
    posts_client: PostsClient, registered_user: tuple[RegistrationData, AuthSession]
) -> None:
    _, user = registered_user
    post = create_post(posts_client, user)
    for response in (posts_client.get(post.id), posts_client.list_for_user(user.user.id)):
        assert_no_password_data(response.json())


def test_complete_post_crud_flow(
    posts_client: PostsClient, registered_user: tuple[RegistrationData, AuthSession]
) -> None:
    _, user = registered_user
    post = create_post(posts_client, user, "create")
    assert Post.model_validate(posts_client.get(post.id).json()["data"]["post"]).content == "create"
    updated = posts_client.update(post.id, "update", user.token)
    assert Post.model_validate(updated.json()["data"]["post"]).content == "update"
    assert posts_client.delete(post.id, user.token).status_code == 200
