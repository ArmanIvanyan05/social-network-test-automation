"""Domain-specific clients without test assertions."""

from collections.abc import Mapping
from typing import Any

import httpx

from social_network_automation.api.client import ApiClient
from social_network_automation.data import RegistrationData


class AuthClient:
    """Verified authentication and profile routes."""

    def __init__(self, client: ApiClient) -> None:
        """Create an authentication client."""
        self._client = client

    def register(self, data: RegistrationData | Mapping[str, Any]) -> httpx.Response:
        """Register a user."""
        payload = data.as_payload() if isinstance(data, RegistrationData) else dict(data)
        return self._client.request("POST", "/users/register", json=payload)

    def login(self, email: str, password: str) -> httpx.Response:
        """Log in with email and password."""
        return self._client.request(
            "POST", "/users/login", json={"email": email, "password": password}
        )

    def login_payload(self, payload: Mapping[str, Any]) -> httpx.Response:
        """Send a login payload for validation tests."""
        return self._client.request("POST", "/users/login", json=dict(payload))

    def current_user(
        self, *, token: str | None = None, authorization: str | None = None
    ) -> httpx.Response:
        """Read the authenticated user."""
        headers = {"Authorization": authorization} if authorization is not None else None
        return self._client.request("GET", "/users/me", token=token, headers=headers)

    def profile(self, user_id: str) -> httpx.Response:
        """Read a public profile."""
        return self._client.get(f"/users/profile/{user_id}")

    def delete_user(self, user_id: str, token: str) -> httpx.Response:
        """Delete the authenticated user's profile."""
        return self._client.request("DELETE", f"/users/profile/{user_id}", token=token)


class PostsClient:
    """Verified post routes."""

    def __init__(self, client: ApiClient) -> None:
        """Create a posts client."""
        self._client = client

    def create(self, content: Any, token: str | None = None) -> httpx.Response:
        """Create a text post."""
        return self._client.request("POST", "/posts", token=token, json={"content": content})

    def get(self, post_id: str) -> httpx.Response:
        """Read a post."""
        return self._client.get(f"/posts/{post_id}")

    def list_for_user(self, user_id: str) -> httpx.Response:
        """List one user's posts."""
        return self._client.get(f"/users/{user_id}/posts")

    def update(self, post_id: str, content: Any, token: str) -> httpx.Response:
        """Update an owned post."""
        return self._client.request(
            "PUT", f"/posts/{post_id}", token=token, json={"content": content}
        )

    def delete(self, post_id: str, token: str) -> httpx.Response:
        """Delete an owned post."""
        return self._client.request("DELETE", f"/posts/{post_id}", token=token)


class CommentsClient:
    """Verified nested comment routes."""

    def __init__(self, client: ApiClient) -> None:
        """Create a comments client."""
        self._client = client

    def create(self, post_id: str, content: Any, token: str | None = None) -> httpx.Response:
        """Create a comment."""
        return self._client.request(
            "POST", f"/posts/{post_id}/comments", token=token, json={"content": content}
        )

    def list(self, post_id: str) -> httpx.Response:
        """List comments for a post."""
        return self._client.get(f"/posts/{post_id}/comments")

    def update(self, post_id: str, comment_id: str, content: Any, token: str) -> httpx.Response:
        """Update an owned comment."""
        return self._client.request(
            "PUT",
            f"/posts/{post_id}/comments/{comment_id}",
            token=token,
            json={"content": content},
        )

    def delete(self, post_id: str, comment_id: str, token: str) -> httpx.Response:
        """Delete an owned comment."""
        return self._client.request(
            "DELETE", f"/posts/{post_id}/comments/{comment_id}", token=token
        )
