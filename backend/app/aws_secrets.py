"""Loads the App Runner config secret into the environment. Off unless AWS_SECRETS_ID is set."""

import json
import os
from typing import Any

from app.log import get_logger

log = get_logger(__name__)

ENV_SWITCH = "AWS_SECRETS_ID"


def _region_of(secret_id: str) -> str | None:
    """The SDK does not read a region out of an ARN; take it from field 3 ourselves."""
    if secret_id.startswith("arn:"):
        parts = secret_id.split(":")
        if len(parts) > 3 and parts[3]:
            return parts[3]
    return os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")


def _fetch(secret_id: str, region: str | None) -> str:
    import boto3  # lazy: local runs and tests never pay for it

    client = boto3.client("secretsmanager", region_name=region)
    response: dict[str, Any] = client.get_secret_value(SecretId=secret_id)
    secret = response.get("SecretString")
    if not isinstance(secret, str):
        raise RuntimeError(f"{secret_id}: secret has no SecretString")
    return secret


def load_aws_secrets(*, override: bool = False, fetch: Any = _fetch) -> list[str]:
    """Merges the secret's flat JSON object into os.environ; returns the keys it set.

    Unset AWS_SECRETS_ID means "not on AWS": nothing happens and .env is read as usual.
    Set, any failure is fatal: a service on half a configuration is worse than none.
    Existing environment variables win unless override=True.
    """
    secret_id = os.environ.get(ENV_SWITCH, "").strip()
    if not secret_id:
        return []
    raw = fetch(secret_id, _region_of(secret_id))
    try:
        values = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{secret_id}: secret is not JSON") from exc
    if not isinstance(values, dict):
        raise RuntimeError(f"{secret_id}: secret must be a JSON object of ENV_VAR -> value")

    applied: list[str] = []
    for key, value in values.items():
        if not override and key in os.environ:
            continue
        os.environ[key] = str(value)
        applied.append(key)
    log.info("aws_secrets_loaded", secret_id=secret_id, keys=sorted(applied))
    return applied
