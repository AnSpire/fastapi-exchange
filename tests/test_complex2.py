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
async def test_full_user_flow_with_market_and_two_users():
    # --- Очистка базы ---
    async for db in get_db():
        await db.execute(Order.__table__.delete())
        await db.execute(Balance.__table__.delete())
        await db.execute(Instrument.__table__.delete())
        await db.execute(User.__table__.delete())
        await db.commit()
        break

    # --- Регистрация двух пользователей ---
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp1 = await ac.post("/api/v1/public/register", json={"name": "testuser1"})
        resp2 = await ac.post("/api/v1/public/register", json={"name": "testuser2"})
        assert resp1.status_code == 200
        assert resp2.status_code == 200
        user1 = resp1.json()
        user2 = resp2.json()
        user1_id, user1_api_key = user1["id"], user1["api_key"]
        user2_id, user2_api_key = user2["id"], user2["api_key"]

    headers1 = {"Authorization": f"TOKEN {user1_api_key}"}
    headers2 = {"Authorization": f"TOKEN {user2_api_key}"}

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

    # --- Пополнение баланса обоим пользователям ---
    # User1: USD (для покупки MEMCOIN)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/v1/admin/balance/deposit", headers=admin_headers, json={
            "user_id": user1_id,
            "ticker": "USD",
            "amount": 1000,
        })
        assert resp.status_code == 200
        assert resp.json() == {"success": True}

    # User2: MEMCOIN (для продажи)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/v1/admin/balance/deposit", headers=admin_headers, json={
            "user_id": user2_id,
            "ticker": ticker,
            "amount": 1000,
        })
        assert resp.status_code == 200
        assert resp.json() == {"success": True}

    # --- Проверка баланса пользователей ---
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        for headers in (headers1, headers2):
            resp = await ac.get("/api/v1/balance", headers=headers)
            assert resp.status_code == 200
            balance = resp.json()
            assert ticker in balance
            assert balance[ticker] == 1000

    # --- Размещение LIMIT и MARKET ордеров двумя пользователями ---
    limit_order_1 = {
        "direction": "BUY",
        "ticker": ticker,
        "qty": 10,
        "price": 50
    }
    market_order_2 = {
        "direction": "SELL",
        "ticker": ticker,
        "qty": 5
        # price для MARKET не указывается
    }

    # User1 размещает LIMIT (BUY)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/v1/order", headers=headers1, json=limit_order_1)
        assert resp.status_code == 200
        order_response1 = resp.json()
        assert "order_id" in order_response1

    # User2 размещает MARKET (SELL)
    market_body2 = dict(market_order_2)
    market_body2["type"] = "MARKET" if "type" in Order.__table__.columns.keys() else None
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/v1/order", headers=headers2, json=market_order_2)
        assert resp.status_code == 200
        order_response2 = resp.json()
        assert "order_id" in order_response2

    # --- Проверка своих ордеров для каждого пользователя ---
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # User1 видит свой LIMIT ордер
        resp = await ac.get("/api/v1/order", headers=headers1)
        assert resp.status_code == 200
        orders = resp.json()
        assert any(o["body"]["ticker"] == ticker and o["body"]["qty"] == 10 for o in orders)

        # User2 видит свой MARKET ордер
        resp = await ac.get("/api/v1/order", headers=headers2)
        assert resp.status_code == 200
        orders = resp.json()
        assert any(o["body"]["ticker"] == ticker and o["body"]["qty"] == 5 for o in orders)

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
