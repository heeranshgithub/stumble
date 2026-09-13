"""The Secrets Manager loader, with the SDK call stubbed out."""

import json
import os

import pytest

from app.aws_secrets import ENV_SWITCH, _region_of, load_aws_secrets

ARN = "arn:aws:secretsmanager:ap-south-1:123456789012:secret:stumble-backend/config-AbCdEf"


def test_off_without_the_switch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_SWITCH, raising=False)

    def boom(*_: object) -> str:
        raise AssertionError("must not be called")

    assert load_aws_secrets(fetch=boom) == []


def test_merges_keys_and_keeps_existing_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_SWITCH, ARN)
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.delenv("MONGODB_DB", raising=False)
    seen: dict[str, object] = {}

    def fake(secret_id: str, region: str | None) -> str:
        seen.update(secret_id=secret_id, region=region)
        return json.dumps({"MONGODB_DB": "stumble", "LOG_LEVEL": "INFO", "PORT": 8000})

    applied = load_aws_secrets(fetch=fake)
    assert seen == {"secret_id": ARN, "region": "ap-south-1"}
    assert sorted(applied) == ["MONGODB_DB", "PORT"]
    assert (os.environ["MONGODB_DB"], os.environ["LOG_LEVEL"], os.environ["PORT"]) == (
        "stumble",
        "DEBUG",
        "8000",
    )


def test_bad_payload_is_fatal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_SWITCH, ARN)
    with pytest.raises(RuntimeError, match="not JSON"):
        load_aws_secrets(fetch=lambda *_: "not json")
    with pytest.raises(RuntimeError, match="JSON object"):
        load_aws_secrets(fetch=lambda *_: "[1, 2]")


def test_region_falls_back_to_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_REGION", "eu-west-3")
    assert _region_of("stumble-backend/config") == "eu-west-3"
    assert _region_of(ARN) == "ap-south-1"
