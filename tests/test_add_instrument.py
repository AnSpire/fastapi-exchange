import pytest
from httpx import AsyncClient, ASGITransport
import uuid
from app.main import app
from app.models.user import User as UserORM
from app.models.instrument import Instrument as InstrumentORM
from app.db.session import async_session_maker

@pytest.mark.asyncio
async def test_create_instrument_admin():
    async with async_session_maker() as session:
        await session.execute(InstrumentORM.__table__.delete())
        await session.execute(UserORM.__table__.delete())
        await session.commit()

        admin = UserORM(
            id=uuid.uuid4(),   # теперь UUID, а не строка!
            name="admininstr",
            role="ADMIN",
            api_key="adminkey"
        )
        session.add(admin)
        await session.commit()

    headers = {"Authorization": "TOKEN adminkey"}
    body = {
        "ticker": "MEMCOIN",
        "name": "Mem Coin"
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Первый вызов — инструмент успешно добавлен
        resp = await ac.post("/api/v1/admin/instrument", headers=headers, json=body)
        assert resp.status_code == 200
        assert resp.json() == {"success": True}

        # Проверим, что инструмент реально добавлен в базе
        async with async_session_maker() as session:
            instrument = await session.get(InstrumentORM, "MEMCOIN")
            assert instrument is not None
            assert instrument.ticker == "MEMCOIN"
            assert instrument.name == "Mem Coin"

        # Повторная вставка должна вызвать ошибку 400
        resp_dup = await ac.post("/api/v1/admin/instrument", headers=headers, json=body)
        assert resp_dup.status_code == 400
        assert resp_dup.json()["detail"] == "Instrument already exists"
