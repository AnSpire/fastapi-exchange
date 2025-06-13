import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.user import User
from app.models.balance import Balance
from app.dependencies import get_db
import uuid

@pytest.mark.asyncio
async def test_admin_deposit_and_withdraw():
    user_name = "test_balance_user"
    ticker = "MEMCOIN"

    # Очищаем пользователя и балансы с этим именем/тикером
    async for db in get_db():
        # Удаляем баланс
        await db.execute(
            Balance.__table__.delete().where(Balance.ticker == ticker)
        )
        # Удаляем пользователя
        await db.execute(
            User.__table__.delete().where(User.name == user_name)
        )
        await db.commit()
        break

    # Создаем пользователя (role=ADMIN, т.к. используем эндпоинты admin)
    test_user_id = uuid.uuid4()
    api_key = f"adminkey-{uuid.uuid4()}"
    async for db in get_db():
        db.add(User(id=test_user_id, name=user_name, api_key=api_key, role="ADMIN"))
        await db.commit()
        break

    headers = {"Authorization": f"TOKEN {api_key}"}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Депозит
        resp = await ac.post("/api/v1/admin/balance/deposit", headers=headers, json={
            "user_id": str(test_user_id),
            "ticker": ticker,
            "amount": 500,
        })
        assert resp.status_code == 200, resp.text
        assert resp.json() == {"success": True}

        # Проверяем, что баланс обновился в базе
        async for db in get_db():
            balance = await db.get(Balance, {"user_id": test_user_id, "ticker": ticker})
            assert balance is not None
            assert balance.amount == 500
            break

        # Вывод части средств
        resp = await ac.post("/api/v1/admin/balance/withdraw", headers=headers, json={
            "user_id": str(test_user_id),
            "ticker": ticker,
            "amount": 200,
        })
        assert resp.status_code == 200, resp.text
        assert resp.json() == {"success": True}

        # Проверяем, что баланс уменьшился
        async for db in get_db():
            balance = await db.get(Balance, {"user_id": test_user_id, "ticker": ticker})
            assert balance.amount == 300
            break

        # Попытка вывести больше, чем есть
        resp = await ac.post("/api/v1/admin/balance/withdraw", headers=headers, json={
            "user_id": str(test_user_id),
            "ticker": ticker,
            "amount": 400,
        })
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Not enough balance"
