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
            id=str(uuid.uuid4()),
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
        resp = await ac.post("/api/v1/admin/instrument", headers=headers, json=body)
        assert resp.status_code == 200
        data = resp.json()
        assert data["ticker"] == "MEMCOIN"
        assert data["name"] == "Mem Coin"

        # Повторная вставка должна вызвать ошибку
        resp_dup = await ac.post("/api/v1/admin/instrument", headers=headers, json=body)
        assert resp_dup.status_code == 400
