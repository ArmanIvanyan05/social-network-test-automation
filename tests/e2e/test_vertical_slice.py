"""Hybrid API/UI workflows across the verified vertical slice."""

from uuid import uuid4

import pytest
from playwright.sync_api import Page, expect

from social_network_automation.api.domain import AuthClient, CommentsClient, PostsClient
from social_network_automation.api.models import AuthSession, Comment, Post
from social_network_automation.cleanup import ResourceTracker
from social_network_automation.config import Settings
from social_network_automation.data import RegistrationData, UserDataFactory
from social_network_automation.ui import LoginPage, PostsPage, SignupPage

pytestmark = [pytest.mark.e2e, pytest.mark.ui, pytest.mark.api, pytest.mark.regression]


@pytest.mark.smoke
def test_api_user_ui_login_reload_logout(
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
    PostsPage(page, settings.frontend_base_url).logout()
    expect(page.get_by_role("heading", name="Log in")).to_be_visible()


def test_api_post_is_modified_in_ui_and_verified_by_api(
    page: Page,
    settings: Settings,
    registered_user: tuple[RegistrationData, AuthSession],
    posts_client: PostsClient,
) -> None:
    data, session = registered_user
    original, updated = f"api-{uuid4().hex}", f"ui-{uuid4().hex}"
    created = Post.model_validate(
        posts_client.create(original, session.token).json()["data"]["post"]
    )
    login = LoginPage(page, settings.frontend_base_url)
    login.open()
    login.login(data.email, data.password)
    posts = PostsPage(page, settings.frontend_base_url)
    expect(posts.post(original)).to_be_visible()
    posts.edit_post(original, updated)
    expect(posts.post(updated)).to_be_visible()
    api_post = Post.model_validate(posts_client.get(created.id).json()["data"]["post"])
    assert api_post.content == updated


@pytest.mark.smoke
def test_ui_registration_post_comment_verified_by_api(
    page: Page,
    settings: Settings,
    auth_client: AuthClient,
    posts_client: PostsClient,
    comments_client: CommentsClient,
    user_data_factory: UserDataFactory,
    resource_tracker: ResourceTracker,
) -> None:
    data = user_data_factory.registration()
    signup = SignupPage(page, settings.frontend_base_url)
    signup.open()
    signup.register(data.username, data.email, data.password)
    posts = PostsPage(page, settings.frontend_base_url)
    expect(page.get_by_role("heading", name="Posts")).to_be_visible()
    token = posts.token()
    assert token is not None
    current = auth_client.current_user(token=token).json()["user"]
    resource_tracker.track(AuthSession(token=token, user=current))
    post_content, comment_content = f"post-{uuid4().hex}", f"comment-{uuid4().hex}"
    posts.create_post(post_content)
    posts.add_comment(post_content, comment_content)
    api_posts = [
        Post.model_validate(item)
        for item in posts_client.list_for_user(current["_id"]).json()["data"]["posts"]
    ]
    post = next(item for item in api_posts if item.content == post_content)
    comments = [
        Comment.model_validate(item)
        for item in comments_client.list(post.id).json()["data"]["comments"]
    ]
    assert comment_content in {comment.content for comment in comments}
