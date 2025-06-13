import pytest
from httpx import AsyncClient, ASGITransport
import uuid

from app.main import app
from app.models.user import User
from app.models.instrument import Instrument
from app.models.balance import Balance
from app.db.session import async_session_maker

@pytest.mark.asyncio
async def test_admin_deposit_and_withdraw():
    # Подготовка: админ, юзер, инструмент
    async with async_session_maker() as session:
        await session.execute(User.__table__.delete())
        await session.execute(Instrument.__table__.delete())
        await session.execute(Balance.__table__.delete())
        await session.commit()
        admin = User(
            id=str(uuid.uuid4()),
            name="admin",
            role="ADMIN",
            api_key="adminkey"
        )
        user = User(
            id=str(uuid.uuid4()),
            name="user",
            role="USER",
            api_key="userkey"
        )
        session.add_all([admin, user])
        instr = Instrument(name="Mem Coin", ticker="MEMCOIN")
        session.add(instr)
        await session.commit()

    admin_headers = {"Authorization": "TOKEN adminkey"}
    body = {"user_id": user.id, "ticker": "MEMCOIN", "amount": 500}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # DEPOSIT
        resp = await ac.post("/api/v1/admin/balance/deposit", json=body, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # Проверить баланс напрямую из БД
        async with async_session_maker() as session:
            bal = await session.get(Balance, {"user_id": user.id, "ticker": "MEMCOIN"})
            assert bal is not None
            assert bal.amount == 500

        # WITHDRAW
        body["amount"] = 300
        resp = await ac.post("/api/v1/admin/balance/withdraw", json=body, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # Проверить баланс снова
        async with async_session_maker() as session:
            bal = await session.get(Balance, {"user_id": user.id, "ticker": "MEMCOIN"})
            assert bal.amount == 200
