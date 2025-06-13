import pytest
from httpx import AsyncClient, ASGITransport
import uuid
import datetime

from app.main import app
from app.models.user import User
from app.models.instrument import Instrument
from app.models.order import Order
from app.db.session import async_session_maker
from app.schemas.order import Level

@pytest.mark.asyncio
async def test_get_orderbook():
    # Чистим БД и добавляем инструмент и ордера
    async with async_session_maker() as session:
        await session.execute(User.__table__.delete())
        await session.execute(Instrument.__table__.delete())
        await session.execute(Order.__table__.delete())
        await session.commit()

        # Добавляем инструмент
        instr = Instrument(name="Mem Coin", ticker="MEMCOIN")
        session.add(instr)

        # Добавляем BUY и SELL лимитные заявки
        session.add_all([
            Order(
                id=str(uuid.uuid4()),
                user_id="user1",
                type="LIMIT",
                direction="BUY",
                ticker="MEMCOIN",
                qty=10,
                price=100,
                status="NEW",
                timestamp=datetime.datetime.utcnow()
            ),
            Order(
                id=str(uuid.uuid4()),
                user_id="user2",
                type="LIMIT",
                direction="SELL",
                ticker="MEMCOIN",
                qty=5,
                price=110,
                status="NEW",
                timestamp=datetime.datetime.utcnow()
            ),
        ])
        await session.commit()

    # Делаем запрос к эндпоинту ордербука
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/public/orderbook/MEMCOIN")
        assert resp.status_code == 200
        data = resp.json()
        assert "bid_levels" in data
        assert "ask_levels" in data

        # Проверяем, что хотя бы по одной заявке с правильной ценой есть в каждом стакане
        assert any(level["price"] == 100 and level["qty"] == 10 for level in data["bid_levels"])
        assert any(level["price"] == 110 and level["qty"] == 5 for level in data["ask_levels"])
