import pytest
from httpx import AsyncClient, ASGITransport
import uuid
from app.main import app
from app.models.user import User as UserORM
from app.models.instrument import Instrument as InstrumentORM
from app.db.session import async_session_maker

@pytest.mark.asyncio
async def test_delete_instrument_admin():
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
        instr = InstrumentORM(ticker="DELME", name="To Delete")
        session.add_all([admin, instr])
        await session.commit()

    headers = {"Authorization": "TOKEN adminkey"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Удаление
        resp = await ac.delete("/api/v1/admin/instrument/DELME", headers=headers)
        assert resp.status_code == 200
        assert resp.json() == {"success": True}

        # Повторное удаление — ошибка
        resp_404 = await ac.delete("/api/v1/admin/instrument/DELME", headers=headers)
        assert resp_404.status_code == 404
