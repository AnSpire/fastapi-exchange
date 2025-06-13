import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.user import User
from app.db.session import async_session_maker

@pytest.mark.asyncio
async def test_create_limit_order():
    async with async_session_maker() as session:
        await session.execute(User.__table__.delete())
        await session.commit()
        user_id = str(uuid.uuid4())
        api_key = "ordkey"
        user = User(id=user_id, name="orderuser", role="USER", api_key=api_key)
        session.add(user)
        await session.commit()

    order_data = {
        "direction": "BUY",
        "ticker": "MEMCOIN",
        "qty": 10,
        "price": 5
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = {"Authorization": f"TOKEN {api_key}"}
        resp = await ac.post("/api/v1/order", json=order_data, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "order_id" in data

@pytest.mark.asyncio
async def test_create_market_order():
   async with async_session_maker() as session:
      await session.execute(User.__table__.delete())
      await session.commit()
      user_id = str(uuid.uuid4())
      api_key = "ordkey"
      user = User(id=user_id, name="orderuser", role="USER", api_key=api_key)
      session.add(user)
      await session.commit()

   order_data = {
      "direction": "BUY",
      "ticker": "MEMCOIN",
      "qty": 10,
   }
   async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
      headers = {"Authorization": f"TOKEN {api_key}"}
      resp = await ac.post("/api/v1/order", json=order_data, headers=headers)
      assert resp.status_code == 200
      data = resp.json()
      assert data["success"] is True
      assert "order_id" in data