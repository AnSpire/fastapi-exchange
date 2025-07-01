import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.user import User
from app.models.balance import Balance
from app.models.instrument import Instrument
from app.models.order import Order
from app.dependencies import get_db
import uuid

@pytest.mark.asyncio
async def test_full_user_flow():
    # --- Очистка базы ---
    async for db in get_db():
        await db.execute(Order.__table__.delete())
        await db.execute(Balance.__table__.delete())
        await db.execute(Instrument.__table__.delete())
        await db.execute(User.__table__.delete())
        await db.commit()
        break

    # --- Регистрация пользователя ---
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/v1/public/register", json={"name": "testuser"})
        assert resp.status_code == 200
        user = resp.json()
        user_id = user["id"]
        api_key = user["api_key"]

    headers = {"Authorization": f"TOKEN {api_key}"}

    # --- Создание администратора и инструмента ---
    admin_api_key = f"adminkey-{uuid.uuid4()}"
    admin_id = uuid.uuid4()
    async for db in get_db():
        db.add(User(id=admin_id, name="admininstr", api_key=admin_api_key, role="ADMIN"))
        await db.commit()
        break

    admin_headers = {"Authorization": f"TOKEN {admin_api_key}"}
    ticker = "MEMCOIN"
    instrument_body = {"ticker": ticker, "name": "Mem Coin"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/v1/admin/instrument", headers=admin_headers, json=instrument_body)
        assert resp.status_code == 200
        assert resp.json() == {"success": True}

    # --- Пополнение баланса пользователю ---
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/v1/admin/balance/deposit", headers=admin_headers, json={
            "user_id": user_id,
            "ticker": ticker,
            "amount": 1000,
        })
        assert resp.status_code == 200
        assert resp.json() == {"success": True}

    # --- Проверка баланса пользователя ---
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/balance", headers=headers)
        assert resp.status_code == 200
        balance = resp.json()
        assert ticker in balance
        assert balance[ticker] == 1000

    # --- Размещение лимитного ордера ---
    order_body = {
        "direction": "BUY",
        "ticker": ticker,
        "qty": 10,
        "price": 50
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/v1/order", headers=headers, json=order_body)
        assert resp.status_code == 200
        order_response = resp.json()
        assert "order_id" in order_response

        # --- Проверка списка ордеров ---
        resp = await ac.get("/api/v1/order", headers=headers)
        assert resp.status_code == 200
        orders = resp.json()
        assert any(o["body"]["ticker"] == ticker for o in orders)

        # --- Проверка ордербука ---
        resp = await ac.get(f"/api/v1/public/orderbook/{ticker}?limit=5")
        assert resp.status_code == 200
        orderbook = resp.json()
        assert "bid_levels" in orderbook and "ask_levels" in orderbook

    # --- Удаление инструмента (admin) ---
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.delete(f"/api/v1/admin/instrument/{ticker}", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json() == {"success": True}
