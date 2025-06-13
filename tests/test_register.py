import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_register_user():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.post("/api/v1/public/register", json={
            "name": "testuser"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["name"] == "testuser"
        assert data["user"]["role"] == "USER"
        assert "id" in data["user"]
        assert "api_key" in data["user"]
        assert len(data["user"]["id"]) >= 32   # Примерная проверка uuid
        assert len(data["user"]["api_key"]) >= 32
