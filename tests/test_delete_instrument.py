import pytest
from httpx import AsyncClient, ASGITransport
import uuid
from app.main import app
from app.models.user import User
from app.models.instrument import Instrument
from app.db.session import async_session_maker

@pytest.mark.asyncio
async def test_delete_instrument():
    # Добавить админа и инструмент
    async with async_session_maker() as session:
        await session.execute(User.__table__.delete())
        await session.execute(Instrument.__table__.delete())
        await session.commit()
        admin_key = "adminkey"
        admin = User(
            id=str(uuid.uuid4()),
            name="admin1",
            role="ADMIN",
            api_key=admin_key
        )
        session.add(admin)
        session.add(Instrument(name="Удалить меня", ticker="DELME"))
        await session.commit()

    # Удалить инструмент через API
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = {"Authorization": f"TOKEN {admin_key}"}
        resp = await ac.delete("/api/v1/admin/instrument/DELME", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    # Проверить, что его больше нет
    async with async_session_maker() as session:
        instrument = await session.get(Instrument, "DELME")
        assert instrument is None
