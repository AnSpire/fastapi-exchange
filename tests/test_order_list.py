import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.user import User
from app.models.order import Order
from app.db.session import async_session_maker

@pytest.mark.asyncio
async def test_list_orders():
    async with async_session_maker() as session:
        await session.execute(User.__table__.delete())
        await session.execute(Order.__table__.delete())
        await session.commit()
        user_id = str(uuid.uuid4())
        api_key = "orderlistkey"
        user = User(id=user_id, name="orderlistuser", role="USER", api_key=api_key)
        session.add(user)
        # Добавить несколько ордеров
        order1 = Order(
            id=str(uuid.uuid4()), user_id=user_id, type="LIMIT", direction="BUY",
            ticker="MEMCOIN", qty=10, price=5, status="NEW"
        )
        order2 = Order(
            id=str(uuid.uuid4()), user_id=user_id, type="MARKET", direction="SELL",
            ticker="DODGE", qty=7, price=None, status="NEW"
        )
        session.add_all([order1, order2])
        await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = {"Authorization": f"TOKEN {api_key}"}
        resp = await ac.get("/api/v1/order", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert any(x["ticker"] == "MEMCOIN" for x in (o["body"] for o in data))
        assert any(x["ticker"] == "DODGE" for x in (o["body"] for o in data))
        # Можно добавить дополнительные проверки структуры
