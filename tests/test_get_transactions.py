import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.transaction import Transaction
from app.models.instrument import Instrument
from app.db.session import async_session_maker
import uuid
import datetime

@pytest.mark.asyncio
async def test_get_transactions():
    async with async_session_maker() as session:
        await session.execute(Transaction.__table__.delete())
        await session.execute(Instrument.__table__.delete())
        await session.commit()
        instr = Instrument(name="Mem Coin", ticker="MEMCOIN")
        session.add(instr)
        # Добавляем сделки
        session.add_all([
            Transaction(
                id=str(uuid.uuid4()),
                ticker="MEMCOIN",
                amount=5,
                price=123,
                timestamp=datetime.datetime.utcnow()
            ),
            Transaction(
                id=str(uuid.uuid4()),
                ticker="MEMCOIN",
                amount=10,
                price=122,
                timestamp=datetime.datetime.utcnow()
            ),
        ])
        await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/public/transactions/MEMCOIN")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        assert data[0]["ticker"] == "MEMCOIN"
