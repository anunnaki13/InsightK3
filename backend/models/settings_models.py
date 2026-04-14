from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OpenRouterSettingsDocument(BaseModel):
    model_config = ConfigDict(extra="ignore")

    key: str = "openrouter"
    provider: str = "openrouter"
    api_key: str = ""
    model: str = ""
    key_label: str | None = None
    key_limit_remaining: float | None = None
    key_usage: float | None = None
    verified_at: datetime | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by: str | None = None


class OpenRouterSettingsUpdate(BaseModel):
    api_key: str = ""
    model: str


class OpenRouterVerifyRequest(BaseModel):
    api_key: str = ""
    model: str | None = None


class OpenRouterSettingsResponse(BaseModel):
    provider: str = "openrouter"
    has_api_key: bool
    masked_api_key: str | None = None
    model: str
    settings_source: str
    verified_at: datetime | None = None
    key_label: str | None = None
    key_limit_remaining: float | None = None
    key_usage: float | None = None
    last_verified_model_exists: bool | None = None
    available_models: list[dict[str, Any]] = Field(default_factory=list)
