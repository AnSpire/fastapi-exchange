import pytest
from httpx import AsyncClient, ASGITransport
import uuid
import datetime
from app.main import app
from app.models.user import User as UserORM
from app.models.instrument import Instrument as InstrumentORM
from app.models.order import Order as OrderORM
from app.db.session import async_session_maker

@pytest.mark.asyncio
async def test_order_endpoints():
    # Подготовим БД: user, instrument
    async with async_session_maker() as session:
        await session.execute(OrderORM.__table__.delete())
        await session.execute(UserORM.__table__.delete())
        await session.execute(InstrumentORM.__table__.delete())
        await session.commit()

        user = UserORM(
            id=str(uuid.uuid4()),
            name="orderuser",
            role="USER",
            api_key="userkey"
        )
        instr = InstrumentORM(name="MEMCOIN", ticker="MEMCOIN")
        session.add_all([user, instr])
        await session.commit()

    headers = {"Authorization": "TOKEN userkey"}

    # 1. Создаём LIMIT ордер
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        body = {
            "direction": "BUY",
            "ticker": "MEMCOIN",
            "qty": 10,
            "price": 123
        }
        resp = await ac.post("/api/v1/order", json=body, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        order_id = data["order_id"]

    # 2. Получаем список ордеров
        resp = await ac.get("/api/v1/order", headers=headers)
        assert resp.status_code == 200
        orders = resp.json()
        assert isinstance(orders, list)
        found = [o for o in orders if o["id"] == order_id]
        assert found, "Созданный ордер не найден в списке"

    #
