"""Faker-backed test data factories."""

from dataclasses import dataclass
from uuid import uuid4

from faker import Faker


@dataclass(frozen=True, slots=True)
class RegistrationData:
    """Valid backend registration fields."""

    username: str
    email: str
    password: str

    def as_payload(self) -> dict[str, str]:
        """Return a JSON-ready registration payload."""
        return {
            "username": self.username,
            "email": self.email,
            "password": self.password,
        }


class UserDataFactory:
    """Generate unique users without shared static identities."""

    def __init__(self, faker: Faker | None = None) -> None:
        """Create the factory with an optional configured Faker instance."""
        self._faker = faker or Faker()

    def registration(self) -> RegistrationData:
        """Build a unique valid registration record."""
        suffix = uuid4().hex[:12]
        return RegistrationData(
            username=f"{self._faker.user_name()}_{suffix}",
            email=f"automation-{suffix}@example.test",
            password=f"Safe-{suffix}-Password1!",
        )
