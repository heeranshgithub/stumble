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

    # real: every key required, refuse to start otherwise. fake: offline stand-ins, only when asked.
    # There is no in-between: a missing key is a startup error, never a silent downgrade.
    providers: Literal["real", "fake"] = "real"

    openrouter_api_key: str | None = None
    openrouter_model: str = ""

    groq_api_key: str | None = None
    groq_stt_model: str = "whisper-large-v3-turbo"

    elevenlabs_api_key: str | None = None
    elevenlabs_voice_id: str | None = None
    elevenlabs_model: str = "eleven_flash_v2_5"

    # A silence this long while the mic is held is a freeze.
    freeze_threshold_ms: int = 3000
    # A card counts as due this many hours early, so "tomorrow" means the next session, not 24h.
    due_window_hours: int = 8

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
