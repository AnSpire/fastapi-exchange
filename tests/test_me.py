import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.user import User
from app.db.session import async_session_maker

@pytest.mark.asyncio
async def test_get_me():
    # Очищаем пользователя перед тестом
    async with async_session_maker() as session:
        await session.execute(User.__table__.delete().where(User.name == "profileuser"))
        await session.commit()
        api_key = "testkey2"
        user = User(
            id=str(uuid.uuid4()),
            name="profileuser",
            role="USER",
            api_key=api_key
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = {"Authorization": f"TOKEN {api_key}"}
        resp = await ac.get("/api/v1/me", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["name"] == "profileuser"
        assert data["user"]["role"] == "USER"
        assert data["user"]["api_key"] == api_key
        assert "id" in data["user"]
