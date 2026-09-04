from datetime import UTC, datetime
from typing import Annotated, Any

from pydantic import (
    AliasChoices,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    field_validator,
)
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    """Base for every model on the wire: snake_case in Python, camelCase in JSON."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    @field_validator("*", mode="after")
    @classmethod
    def _utc_datetimes(cls, value: Any) -> Any:
        """Wire datetimes always carry an offset and millisecond precision, matching what Mongo
        stores, so a value is identical before and after a round trip. Naive means UTC."""
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=UTC)
            return value.replace(microsecond=value.microsecond // 1000 * 1000)
        return value


class RequestModel(ApiModel):
    """Request bodies reject unknown fields: a typo is a 422, not a silently ignored write."""

    model_config = ConfigDict(extra="forbid", **ApiModel.model_config)


def _stringify_id(value: Any) -> Any:
    return str(value) if value is not None else value


MongoId = Annotated[str, BeforeValidator(_stringify_id)]


class MongoModel(ApiModel):
    """A DTO built from a Mongo document: accepts `_id` on input, emits `id` on the wire."""

    id: MongoId | None = Field(
        default=None,
        validation_alias=AliasChoices("_id", "id"),
        serialization_alias="id",
    )
