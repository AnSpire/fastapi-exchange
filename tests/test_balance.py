import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.user import User
from app.models.balance import Balance
from app.db.session import async_session_maker

@pytest.mark.asyncio
async def test_get_balance():
    async with async_session_maker() as session:
        await session.execute(User.__table__.delete())
        await session.execute(Balance.__table__.delete())
        await session.commit()
        user_id = str(uuid.uuid4())
        api_key = "testkey"
        user = User(id=user_id, name="baluser", role="USER", api_key=api_key)
        session.add(user)
        session.add_all([
            Balance(user_id=user_id, ticker="MEMCOIN", amount=123),
            Balance(user_id=user_id, ticker="DODGE", amount=456)
        ])
        await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = {"Authorization": f"TOKEN {api_key}"}
        resp = await ac.get("/api/v1/balance", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["MEMCOIN"] == 123
        assert data["DODGE"] == 456
