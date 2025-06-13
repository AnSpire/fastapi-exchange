import pytest
from httpx import AsyncClient, ASGITransport
import uuid
from app.main import app
from app.models.user import User
from app.models.instrument import Instrument
from app.db.session import async_session_maker

@pytest.mark.asyncio
async def test_add_instrument():
    # Создать админа
    async with async_session_maker() as session:
        await session.execute(User.__table__.delete())
        await session.execute(Instrument.__table__.delete())
        await session.commit()
        admin_key = "adminkey"
        admin = User(
            id=str(uuid.uuid4()),
            name="admin",
            role="ADMIN",
            api_key=admin_key
        )
        session.add(admin)
        await session.commit()
        await session.refresh(admin)

    # Сделать запрос на создание инструмента
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = {"Authorization": f"TOKEN {admin_key}"}
        body = {"name": "Test Coin1", "ticker": "TSTCOIN1"}
        resp = await ac.post("/api/v1/admin/instrument", json=body, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    # Проверить, что в базе появился тикер
    async with async_session_maker() as session:
        instrument = await session.get(Instrument, "TSTCOIN1")
        assert instrument is not None
        assert instrument.name == "Test Coin1"
