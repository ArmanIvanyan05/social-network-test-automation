"""High-value UI tests for text posts and comments."""

from uuid import uuid4

import pytest
from playwright.sync_api import Page, expect

from social_network_automation.api.models import AuthSession
from social_network_automation.config import Settings
from social_network_automation.data import RegistrationData
from social_network_automation.ui import LoginPage, PostsPage

pytestmark = [pytest.mark.ui, pytest.mark.regression]


def open_posts(
    page: Page, settings: Settings, registered_user: tuple[RegistrationData, AuthSession]
) -> PostsPage:
    """Log in and return the supported posts page."""
    data, _ = registered_user
    login = LoginPage(page, settings.frontend_base_url)
    login.open()
    login.login(data.email, data.password)
    posts = PostsPage(page, settings.frontend_base_url)
    expect(page.get_by_role("heading", name="Posts")).to_be_visible()
    return posts


def unique(prefix: str) -> str:
    """Return unique visible content."""
    return f"{prefix}-{uuid4().hex}"


def test_create_and_display_post(
    page: Page, settings: Settings, registered_user: tuple[RegistrationData, AuthSession]
) -> None:
    posts = open_posts(page, settings, registered_user)
    content = unique("created")
    posts.create_post(content)
    expect(posts.post(content)).to_be_visible()


def test_edit_owned_post(
    page: Page, settings: Settings, registered_user: tuple[RegistrationData, AuthSession]
) -> None:
    posts = open_posts(page, settings, registered_user)
    original, updated = unique("original"), unique("updated")
    posts.create_post(original)
    posts.edit_post(original, updated)
    expect(posts.post(updated)).to_be_visible()


def test_delete_owned_post(
    page: Page, settings: Settings, registered_user: tuple[RegistrationData, AuthSession]
) -> None:
    posts = open_posts(page, settings, registered_user)
    content = unique("delete")
    posts.create_post(content)
    posts.delete_post(content)
    expect(posts.post(content)).to_have_count(0)


def test_empty_post_shows_validation_error(
    page: Page, settings: Settings, registered_user: tuple[RegistrationData, AuthSession]
) -> None:
    posts = open_posts(page, settings, registered_user)
    posts.create_post("")
    expect(page.get_by_role("alert")).to_have_text("Post content is required")


def test_create_and_display_comment(
    page: Page, settings: Settings, registered_user: tuple[RegistrationData, AuthSession]
) -> None:
    posts = open_posts(page, settings, registered_user)
    post, comment = unique("post"), unique("comment")
    posts.create_post(post)
    posts.add_comment(post, comment)
    expect(posts.comment_item(post, comment)).to_be_visible()


def test_edit_owned_comment(
    page: Page, settings: Settings, registered_user: tuple[RegistrationData, AuthSession]
) -> None:
    posts = open_posts(page, settings, registered_user)
    post, original, updated = unique("post"), unique("comment"), unique("edited")
    posts.create_post(post)
    posts.add_comment(post, original)
    posts.edit_comment(post, original, updated)
    expect(posts.comment_item(post, updated)).to_be_visible()


def test_delete_owned_comment(
    page: Page, settings: Settings, registered_user: tuple[RegistrationData, AuthSession]
) -> None:
    posts = open_posts(page, settings, registered_user)
    post, comment = unique("post"), unique("comment")
    posts.create_post(post)
    posts.add_comment(post, comment)
    posts.delete_comment(post, comment)
    expect(posts.comment_item(post, comment)).to_have_count(0)


def test_empty_comment_shows_validation_error(
    page: Page, settings: Settings, registered_user: tuple[RegistrationData, AuthSession]
) -> None:
    posts = open_posts(page, settings, registered_user)
    post = unique("post")
    posts.create_post(post)
    posts.add_comment(post, "")
    expect(page.get_by_role("alert")).to_have_text("Comment content is required")
