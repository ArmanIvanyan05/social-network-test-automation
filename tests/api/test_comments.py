"""Comments API behavior and ownership tests."""

from uuid import uuid4

import pytest

from social_network_automation.api.domain import AuthClient, CommentsClient, PostsClient
from social_network_automation.api.models import AuthSession, Comment
from social_network_automation.assertions import assert_error
from social_network_automation.cleanup import ResourceTracker
from social_network_automation.data import RegistrationData, UserDataFactory
from tests.api.test_posts import create_post

pytestmark = [pytest.mark.api, pytest.mark.regression]


def create_comment(
    comments: CommentsClient, post_id: str, session: AuthSession, content: str | None = None
) -> Comment:
    """Create and parse one comment."""
    response = comments.create(post_id, content or f"comment-{uuid4().hex}", session.token)
    assert response.status_code == 201
    return Comment.model_validate(response.json()["data"]["comment"])


def test_create_comment(
    comments_client: CommentsClient,
    posts_client: PostsClient,
    registered_user: tuple[RegistrationData, AuthSession],
) -> None:
    _, user = registered_user
    post = create_post(posts_client, user)
    comment = create_comment(comments_client, post.id, user, "Useful comment")
    assert comment.content == "Useful comment"
    assert comment.post == post.id


def test_list_comments(
    comments_client: CommentsClient,
    posts_client: PostsClient,
    registered_user: tuple[RegistrationData, AuthSession],
) -> None:
    _, user = registered_user
    post = create_post(posts_client, user)
    created = create_comment(comments_client, post.id, user)
    response = comments_client.list(post.id)
    comments = [Comment.model_validate(item) for item in response.json()["data"]["comments"]]
    assert response.status_code == 200
    assert created.id in {comment.id for comment in comments}


def test_update_owned_comment(
    comments_client: CommentsClient,
    posts_client: PostsClient,
    registered_user: tuple[RegistrationData, AuthSession],
) -> None:
    _, user = registered_user
    post = create_post(posts_client, user)
    comment = create_comment(comments_client, post.id, user)
    response = comments_client.update(post.id, comment.id, "updated", user.token)
    assert response.status_code == 200
    assert Comment.model_validate(response.json()["data"]["comment"]).content == "updated"


def test_delete_owned_comment(
    comments_client: CommentsClient,
    posts_client: PostsClient,
    registered_user: tuple[RegistrationData, AuthSession],
) -> None:
    _, user = registered_user
    post = create_post(posts_client, user)
    comment = create_comment(comments_client, post.id, user)
    assert comments_client.delete(post.id, comment.id, user.token).status_code == 200
    assert_error(comments_client.delete(post.id, comment.id, user.token), 404, "COMMENT_NOT_FOUND")


def test_reject_empty_comment(
    comments_client: CommentsClient,
    posts_client: PostsClient,
    registered_user: tuple[RegistrationData, AuthSession],
) -> None:
    _, user = registered_user
    post = create_post(posts_client, user)
    assert_error(comments_client.create(post.id, " ", user.token), 400, "VALIDATION_ERROR")


def test_comment_creation_requires_authentication(
    comments_client: CommentsClient,
    posts_client: PostsClient,
    registered_user: tuple[RegistrationData, AuthSession],
) -> None:
    _, user = registered_user
    post = create_post(posts_client, user)
    assert_error(comments_client.create(post.id, "protected"), 401, "MISSING_TOKEN")


def test_reject_malformed_comment_id(
    comments_client: CommentsClient,
    posts_client: PostsClient,
    registered_user: tuple[RegistrationData, AuthSession],
) -> None:
    _, user = registered_user
    post = create_post(posts_client, user)
    assert_error(
        comments_client.update(post.id, "not-an-id", "x", user.token),
        400,
        "INVALID_COMMENT_ID",
    )


def test_missing_comment_returns_not_found(
    comments_client: CommentsClient,
    posts_client: PostsClient,
    registered_user: tuple[RegistrationData, AuthSession],
) -> None:
    _, user = registered_user
    post = create_post(posts_client, user)
    assert_error(
        comments_client.delete(post.id, "507f1f77bcf86cd799439011", user.token),
        404,
        "COMMENT_NOT_FOUND",
    )


def second_user(
    auth: AuthClient, factory: UserDataFactory, tracker: ResourceTracker
) -> AuthSession:
    """Create another tracked user."""
    return tracker.track(AuthSession.model_validate(auth.register(factory.registration()).json()))


def test_other_user_cannot_update_comment(
    comments_client: CommentsClient,
    posts_client: PostsClient,
    registered_user: tuple[RegistrationData, AuthSession],
    auth_client: AuthClient,
    user_data_factory: UserDataFactory,
    resource_tracker: ResourceTracker,
) -> None:
    _, owner = registered_user
    other = second_user(auth_client, user_data_factory, resource_tracker)
    post = create_post(posts_client, owner)
    comment = create_comment(comments_client, post.id, owner)
    assert_error(
        comments_client.update(post.id, comment.id, "stolen", other.token),
        403,
        "COMMENT_FORBIDDEN",
    )


def test_other_user_cannot_delete_comment(
    comments_client: CommentsClient,
    posts_client: PostsClient,
    registered_user: tuple[RegistrationData, AuthSession],
    auth_client: AuthClient,
    user_data_factory: UserDataFactory,
    resource_tracker: ResourceTracker,
) -> None:
    _, owner = registered_user
    other = second_user(auth_client, user_data_factory, resource_tracker)
    post = create_post(posts_client, owner)
    comment = create_comment(comments_client, post.id, owner)
    assert_error(comments_client.delete(post.id, comment.id, other.token), 403, "COMMENT_FORBIDDEN")


def test_missing_parent_post_is_rejected(
    comments_client: CommentsClient, registered_user: tuple[RegistrationData, AuthSession]
) -> None:
    _, user = registered_user
    assert_error(
        comments_client.create("507f1f77bcf86cd799439011", "orphan", user.token),
        404,
        "POST_NOT_FOUND",
    )


def test_complete_post_comment_update_delete_flow(
    comments_client: CommentsClient,
    posts_client: PostsClient,
    registered_user: tuple[RegistrationData, AuthSession],
) -> None:
    _, user = registered_user
    post = create_post(posts_client, user)
    comment = create_comment(comments_client, post.id, user, "initial")
    updated = comments_client.update(post.id, comment.id, "final", user.token)
    assert Comment.model_validate(updated.json()["data"]["comment"]).content == "final"
    assert comments_client.delete(post.id, comment.id, user.token).status_code == 200
