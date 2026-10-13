"""Pydantic schemas for user registration, authentication, and user profiles."""

from __future__ import annotations

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class RegisterRequest(BaseModel):
    email: str = Field(..., max_length=255, description="Valid user email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password with min 8 chars and numbers/symbols")
    full_name: str | None = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    email: str = Field(..., max_length=255)
    password: str = Field(..., max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str | None
    role: str
    created_at: datetime


class AuthResponse(BaseModel):
    token: str
    user: UserOut
