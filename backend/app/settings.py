from typing import Any, Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

_SECRET_MARKERS = ("key", "secret", "token", "password", "uri", "url")


class Settings(BaseSettings):
    """The only place that reads the environment."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    env: Literal["dev", "prod", "test"] = "dev"

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "stumble"

    cors_origins_raw: str = Field(default="http://localhost:3000", validation_alias="cors_origins")

    openrouter_api_key: str | None = None
    openrouter_model: str = ""

    groq_api_key: str | None = None

    elevenlabs_api_key: str | None = None
    elevenlabs_voice_id: str | None = None
    tts_provider: Literal["elevenlabs", "browser"] = "elevenlabs"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins_raw.split(",") if o.strip()]

    def redact(self) -> dict[str, Any]:
        """Settings safe to log at startup: any secret-looking field is masked."""
        out: dict[str, Any] = {}
        for name, value in self.model_dump().items():
            if any(marker in name for marker in _SECRET_MARKERS) and value:
                out[name] = "***"
            else:
                out[name] = value
        return out
