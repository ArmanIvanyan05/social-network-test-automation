"""Typed API contracts for verified backend resources."""

from pydantic import BaseModel, ConfigDict, Field


class User(BaseModel):
    """Password-free backend user."""

    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(alias="_id")
    username: str
    email: str


class AuthSession(BaseModel):
    """Successful registration or login response."""

    token: str
    user: User


class Author(User):
    """Serialized post or comment author."""


class Post(BaseModel):
    """Verified text post response."""

    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(alias="_id")
    content: str
    author: Author
    created_at: str = Field(alias="createdAt")


class Comment(BaseModel):
    """Verified comment response."""

    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(alias="_id")
    content: str
    author: Author
    post: str


class ErrorResponse(BaseModel):
    """Structured backend error."""

    status: str
    code: str
    message: str
