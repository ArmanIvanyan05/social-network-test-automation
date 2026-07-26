"""API-based deterministic test-data cleanup."""

from dataclasses import dataclass

from social_network_automation.api.domain import AuthClient, PostsClient
from social_network_automation.api.models import AuthSession, Post


@dataclass(frozen=True, slots=True)
class CleanupUser:
    """User identity needed for API cleanup."""

    id: str
    token: str


class ResourceTracker:
    """Track generated users and remove their posts before their profiles."""

    def __init__(self, auth: AuthClient, posts: PostsClient) -> None:
        """Create a tracker backed only by supported APIs."""
        self._auth = auth
        self._posts = posts
        self._users: list[CleanupUser] = []

    def track(self, session: AuthSession) -> AuthSession:
        """Track a created session and return it for fluent fixture setup."""
        self._users.append(CleanupUser(session.user.id, session.token))
        return session

    def cleanup(self) -> None:
        """Remove generated posts and users, surfacing every cleanup failure."""
        failures: list[str] = []
        for user in reversed(self._users):
            listing = self._posts.list_for_user(user.id)
            if listing.status_code == 200:
                posts = [
                    Post.model_validate(item)
                    for item in listing.json().get("data", {}).get("posts", [])
                ]
                for post in posts:
                    deletion = self._posts.delete(post.id, user.token)
                    if deletion.status_code not in {200, 404}:
                        failures.append(
                            f"post {post.id}: HTTP {deletion.status_code} {deletion.text}"
                        )
            elif listing.status_code != 404:
                failures.append(f"list posts for {user.id}: HTTP {listing.status_code}")
            deletion = self._auth.delete_user(user.id, user.token)
            if deletion.status_code not in {200, 404}:
                failures.append(f"user {user.id}: HTTP {deletion.status_code} {deletion.text}")
        if failures:
            raise AssertionError("Cleanup failed:\n" + "\n".join(failures))
