import pytest
from httpx import AsyncClient, ASGITransport
import uuid
import datetime
from app.main import app
from app.models.instrument import Instrument as InstrumentORM
from app.models.order import Order as OrderORM
from app.db.session import async_session_maker

@pytest.mark.asyncio
async def test_get_orderbook():
    async with async_session_maker() as session:
        await session.execute(OrderORM.__table__.delete())
        await session.execute(InstrumentORM.__table__.delete())
        await session.commit()

        # Добавляем инструмент
        instr = InstrumentORM(ticker="MEMCOIN", name="Mem Coin")
        session.add(instr)

        # Добавляем заявки: 2 BID (цена выше — приоритет), 2 ASK (цена ниже — приоритет)
        session.add_all([
            OrderORM(
                id=str(uuid.uuid4()), user_id=str(uuid.uuid4()),
                type="LIMIT", direction="BUY",
                ticker="MEMCOIN", qty=10, price=105, status="NEW",
                timestamp=datetime.datetime.utcnow()
            ),
            OrderORM(
                id=str(uuid.uuid4()), user_id=str(uuid.uuid4()),
                type="LIMIT", direction="BUY",
                ticker="MEMCOIN", qty=5, price=100, status="NEW",
                timestamp=datetime.datetime.utcnow()
            ),
            OrderORM(
                id=str(uuid.uuid4()), user_id=str(uuid.uuid4()),
                type="LIMIT", direction="SELL",
                ticker="MEMCOIN", qty=3, price=110, status="NEW",
                timestamp=datetime.datetime.utcnow()
            ),
            OrderORM(
                id=str(uuid.uuid4()), user_id=str(uuid.uuid4()),
                type="LIMIT", direction="SELL",
                ticker="MEMCOIN", qty=4, price=115, status="NEW",
                timestamp=datetime.datetime.utcnow()
            ),
        ])
        await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/public/orderbook/MEMCOIN?limit=2")
        assert resp.status_code == 200
        data = resp.json()
        assert "bid_levels" in data
        assert "ask_levels" in data
        # Проверяем сортировку
        assert data["bid_levels"][0]["price"] > data["bid_levels"][1]["price"]
        assert data["ask_levels"][0]["price"] < data["ask_levels"][1]["price"]
        assert len(data["bid_levels"]) == 2
        assert len(data["ask_levels"]) == 2
        # Проверка данных
        assert any(level["price"] == 105 and level["qty"] == 10 for level in data["bid_levels"])
        assert any(level["price"] == 110 and level["qty"] == 3 for level in data["ask_levels"])

    # Проверяем 404 для несуществующего инструмента
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("api/v1/public/orderbook/NOCOIN")
        assert resp.status_code == 404
