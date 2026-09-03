from httpx import AsyncClient


def _assert_envelope(body: dict[str, object], code: str) -> None:
    assert set(body) == {"error"}
    error = body["error"]
    assert isinstance(error, dict)
    assert set(error) >= {"code", "message", "details"}
    assert error["code"] == code
    assert isinstance(error["details"], dict)
    assert error["details"]["requestId"]


async def test_unknown_route_uses_envelope(client: AsyncClient) -> None:
    res = await client.get("/nope")
    assert res.status_code == 404
    _assert_envelope(res.json(), "not_found")


async def test_missing_device_id_is_400(client: AsyncClient) -> None:
    res = await client.get("/today")
    assert res.status_code == 400
    _assert_envelope(res.json(), "device_id_required")


async def test_request_id_is_echoed(client: AsyncClient) -> None:
    res = await client.get("/nope", headers={"X-Request-Id": "abc-123"})
    assert res.headers["x-request-id"] == "abc-123"
    assert res.json()["error"]["details"]["requestId"] == "abc-123"
