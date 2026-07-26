"""Page objects for the supported frontend vertical slice."""

from playwright.sync_api import Locator, Page

TOKEN_KEY = "social_network_auth_token"


class SignupPage:
    """Registration entry page."""

    def __init__(self, page: Page, base_url: str) -> None:
        """Bind the page object."""
        self.page = page
        self.url = base_url

    def open(self) -> None:
        """Open registration."""
        self.page.goto(self.url, wait_until="domcontentloaded")

    def register(self, username: str, email: str, password: str) -> None:
        """Submit registration fields."""
        self.page.locator('input[name="username"]').fill(username)
        self.page.locator('input[name="email"]').fill(email)
        self.page.locator('input[name="password"]').fill(password)
        self.page.get_by_role("button", name="Create account").click()

    def submit_empty(self) -> None:
        """Submit the empty form."""
        self.page.get_by_role("button", name="Create account").click()


class LoginPage:
    """Login page interactions."""

    def __init__(self, page: Page, base_url: str) -> None:
        """Bind the page object."""
        self.page = page
        self.url = f"{base_url}/login"

    def open(self) -> None:
        """Open login."""
        self.page.goto(self.url, wait_until="domcontentloaded")

    def login(self, email: str, password: str) -> None:
        """Submit login credentials."""
        self.page.locator('input[name="email"]').fill(email)
        self.page.locator('input[name="password"]').fill(password)
        self.page.get_by_role("button", name="Log in").click()

    def submit_empty(self) -> None:
        """Submit the empty form."""
        self.page.get_by_role("button", name="Log in").click()


class PostsPage:
    """Posts and nested comments page interactions."""

    def __init__(self, page: Page, base_url: str) -> None:
        """Bind the page object."""
        self.page = page
        self.url = f"{base_url}/profile/posts"

    def open(self) -> None:
        """Open the protected posts page."""
        self.page.goto(self.url, wait_until="domcontentloaded")

    def create_post(self, content: str) -> None:
        """Create a text post."""
        self.page.get_by_label("What's on your mind?").fill(content)
        self.page.get_by_role("button", name="Create post").click()

    def post(self, content: str) -> Locator:
        """Locate a post article by unique content."""
        return self.page.get_by_role("article").filter(has_text=content)

    def edit_post(self, old_content: str, new_content: str) -> None:
        """Edit an owned post."""
        article = self.post(old_content)
        article.get_by_role("button", name="Edit post").click()
        editor = self.page.get_by_label("Edit post")
        editor.fill(new_content)
        editor.locator("xpath=ancestor::form").get_by_role("button", name="Save post").click()

    def delete_post(self, content: str) -> None:
        """Delete an owned post."""
        self.post(content).get_by_role("button", name="Delete post").click()

    def add_comment(self, post_content: str, comment: str) -> None:
        """Add a comment to a post."""
        article = self.post(post_content)
        article.get_by_label("Add a comment").fill(comment)
        article.get_by_role("button", name="Comment", exact=True).click()

    def comment_item(self, post_content: str, comment: str) -> Locator:
        """Locate a comment list item."""
        return self.post(post_content).get_by_role("listitem").filter(has_text=comment)

    def edit_comment(self, post_content: str, old: str, new: str) -> None:
        """Edit an owned comment."""
        item = self.comment_item(post_content, old)
        item.get_by_role("button", name="Edit comment").click()
        editor = self.post(post_content).get_by_label("Edit comment")
        editor.fill(new)
        editor.locator("xpath=ancestor::form").get_by_role("button", name="Save comment").click()

    def delete_comment(self, post_content: str, comment: str) -> None:
        """Delete an owned comment."""
        self.comment_item(post_content, comment).get_by_role(
            "button", name="Delete comment"
        ).click()

    def logout(self) -> None:
        """Clear the frontend session through the UI."""
        self.page.get_by_role("button", name="Log out").click()

    def token(self) -> str | None:
        """Read the application token for test cleanup only."""
        value = self.page.evaluate("(key) => localStorage.getItem(key)", TOKEN_KEY)
        return value if isinstance(value, str) else None
