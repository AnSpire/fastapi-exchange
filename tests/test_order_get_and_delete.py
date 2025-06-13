import pytest
from httpx import AsyncClient, ASGITransport
import uuid
import datetime

from app.main import app
from app.models.user import User
from app.models.instrument import Instrument
from app.models.order import Order
from app.db.session import async_session_maker

@pytest.mark.asyncio
async def test_order_get_and_delete():
    # Подготовка: добавить пользователя, инструмент и ордер
    async with async_session_maker() as session:
        await session.execute(User.__table__.delete())
        await session.execute(Instrument.__table__.delete())
        await session.execute(Order.__table__.delete())
        await session.commit()

        user = User(
            id=str(uuid.uuid4()),
            name="test_user",
            role="USER",
            api_key="userkey"
        )
        session.add(user)
        instr = Instrument(name="Mem Coin", ticker="MEMCOIN")
        session.add(instr)
        order = Order(
            id=str(uuid.uuid4()),
            user_id=user.id,
            type="LIMIT",
            direction="BUY",
            ticker="MEMCOIN",
            qty=10,
            price=100,
            status="NEW",
            timestamp=datetime.datetime.utcnow()
        )
        session.add(order)
        await session.commit()

    headers = {"Authorization": "TOKEN userkey"}
    # GET
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/order/{order.id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == order.id
        assert data["status"] == "NEW"

        # DELETE
        resp = await ac.delete(f"/api/v1/order/{order.id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # Проверить, что статус изменился
        # (можно через отдельный get или прямой доступ к БД)
