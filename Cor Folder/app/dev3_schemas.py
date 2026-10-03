from typing import Literal

import re

from pydantic import BaseModel, Field, field_validator


SUPPORTED_LANGUAGES = {"en", "hi", "or"}
UserRole = Literal["TOURIST", "CONTRIBUTOR", "MODERATOR", "GOVERNMENT_ADMIN", "SUPER_ADMIN"]


def validate_language(value: str) -> str:
    if value not in SUPPORTED_LANGUAGES:
        raise ValueError("language must be one of: en, hi, or")
    return value


class RegisterInput(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=10, max_length=128)
    display_name: str = Field(min_length=1, max_length=80)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("email must be a valid address")
        return value

    @field_validator("display_name")
    @classmethod
    def clean_display_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("display_name cannot be blank")
        return value


class LoginInput(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("email must be a valid address")
        return value


class ProfilePatch(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=80)
    bio: str | None = Field(default=None, max_length=1000)

    @field_validator("display_name")
    @classmethod
    def clean_display_name(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("display_name cannot be blank")
        return value.strip() if value is not None else value


class PreferencesPatch(BaseModel):
    language: str | None = None
    theme: Literal["light", "dark", "system"] | None = None
    voice_enabled: bool | None = None
    units: Literal["metric", "imperial"] | None = None

    @field_validator("language")
    @classmethod
    def supported_language(cls, value: str | None) -> str | None:
        return validate_language(value) if value is not None else value


class SubmissionCreate(BaseModel):
    type: Literal["restaurant", "hotel", "temple", "tourist_spot", "facility", "local_attraction", "travel_tip"]
    name: str = Field(min_length=2, max_length=160)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    description: str = Field(min_length=10, max_length=5000)
    photos: list[str] = Field(default_factory=list, max_length=8)
    language: str = "en"

    @field_validator("name", "description")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value cannot be blank")
        return value.strip()

    @field_validator("language")
    @classmethod
    def supported_language(cls, value: str) -> str:
        return validate_language(value)

    @field_validator("photos")
    @classmethod
    def validate_photos(cls, value: list[str]) -> list[str]:
        from urllib.parse import urlparse
        for photo in value:
            parsed = urlparse(photo)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc or len(photo) > 2048:
                raise ValueError("photos must be valid http(s) URLs")
        return value


class ReviewCreate(BaseModel):
    place_id: str = Field(min_length=1, max_length=255)
    rating: int = Field(ge=1, le=5)
    comment: str = Field(default="", max_length=3000)

    @field_validator("place_id")
    @classmethod
    def clean_place_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("place_id cannot be blank")
        return value


class ModerationDecision(BaseModel):
    note: str = Field(default="", max_length=1000)


class PlaceContentInput(BaseModel):
    language: str
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    rules: str = Field(default="", max_length=3000)
    tips: str = Field(default="", max_length=3000)
    source: Literal["community", "official", "editorial"] = "community"

    @field_validator("language")
    @classmethod
    def supported_language(cls, value: str) -> str:
        return validate_language(value)


class TranslateInput(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    source_language: str
    target_language: str

    @field_validator("text")
    @classmethod
    def clean_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text cannot be blank")
        return value.strip()

    @field_validator("source_language", "target_language")
    @classmethod
    def supported_language(cls, value: str) -> str:
        return validate_language(value)


class QueryInput(BaseModel):
    text: str = Field(min_length=2, max_length=1000)

    @field_validator("text")
    @classmethod
    def clean_text(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("text must contain at least two non-space characters")
        return value


class AudioInput(BaseModel):
    audio_base64: str = Field(min_length=16, max_length=10_000_000)
    content_type: Literal["audio/wav", "audio/mpeg", "audio/mp4", "audio/webm", "audio/ogg"]
    language: str | None = None

    @field_validator("language")
    @classmethod
    def supported_language(cls, value: str | None) -> str | None:
        return validate_language(value) if value is not None else value


class RolePatch(BaseModel):
    role: UserRole
