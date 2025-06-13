import pytest
from httpx import AsyncClient, ASGITransport
import uuid
import datetime
from app.main import app
from app.models.instrument import Instrument as InstrumentORM
from app.models.transaction import Transaction as TransactionORM
from app.db.session import async_session_maker

@pytest.mark.asyncio
async def test_get_transaction_history():
    async with async_session_maker() as session:
        await session.execute(TransactionORM.__table__.delete())
        await session.execute(InstrumentORM.__table__.delete())
        await session.commit()

        instr = InstrumentORM(ticker="MEMCOIN", name="Mem Coin")
        session.add(instr)

        session.add_all([
            TransactionORM(
                id=str(uuid.uuid4()), ticker="MEMCOIN", amount=3, price=100,
                timestamp=datetime.datetime.utcnow()
            ),
            TransactionORM(
                id=str(uuid.uuid4()), ticker="MEMCOIN", amount=2, price=105,
                timestamp=datetime.datetime.utcnow()
            )
        ])
        await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/public/transactions/MEMCOIN?limit=2")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert all("ticker" in tx and "amount" in tx and "price" in tx and "timestamp" in tx for tx in data)

    # 404 для несуществующего тикера
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/public/transactions/UNKNOWN")
        assert resp.status_code == 404
