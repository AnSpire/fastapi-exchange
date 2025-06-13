import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.instrument import Instrument as InstrumentORM
from app.db.session import async_session_maker

@pytest.mark.asyncio
async def test_list_instruments():
    async with async_session_maker() as session:
        await session.execute(InstrumentORM.__table__.delete())
        await session.commit()
        instr1 = InstrumentORM(ticker="BTC", name="Bitcoin")
        instr2 = InstrumentORM(ticker="ETH", name="Ethereum")
        session.add_all([instr1, instr2])
        await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/public/instrument")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert {"name": "Bitcoin", "ticker": "BTC"} in data
        assert {"name": "Ethereum", "ticker": "ETH"} in data
