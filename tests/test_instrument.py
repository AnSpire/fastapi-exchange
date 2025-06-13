import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.instrument import Instrument
from app.db.session import async_session_maker

@pytest.mark.asyncio
async def test_get_instruments():
    async with async_session_maker() as session:
        # Очистим таблицу и добавим тестовые инструменты
        await session.execute(Instrument.__table__.delete())
        session.add_all([
            Instrument(name="Мемкоин", ticker="MEMCOIN"),
            Instrument(name="Додж", ticker="DODGE")
        ])
        await session.commit()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/public/instrument")
        assert resp.status_code == 200
        data = resp.json()
        assert any(x["ticker"] == "MEMCOIN" for x in data)
        assert any(x["ticker"] == "DODGE" for x in data)
