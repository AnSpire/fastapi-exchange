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
async def test_order_matching_and_balances():
    # --- Очистка базы ---
    async for db in get_db():
        await db.execute(Order.__table__.delete())
        await db.execute(Balance.__table__.delete())
        await db.execute(Instrument.__table__.delete())
        await db.execute(User.__table__.delete())
        await db.commit()
        break

    # --- Создание двух пользователей ---
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp1 = await ac.post("/api/v1/public/register", json={"name": "buyer"})
        resp2 = await ac.post("/api/v1/public/register", json={"name": "seller"})
        user1 = resp1.json()
        user2 = resp2.json()
        id1 = str(user1["id"])  # явно строка!
        id2 = str(user2["id"])
        key1 = user1["api_key"]
        key2 = user2["api_key"]

    headers1 = {"Authorization": f"TOKEN {key1}"}
    headers2 = {"Authorization": f"TOKEN {key2}"}

    # --- Создание администратора и инструмента ---
    admin_api_key = f"adminkey-{uuid.uuid4()}"
    admin_id = str(uuid.uuid4())  # строка, если вдруг где-то понадобилось
    async for db in get_db():
        db.add(User(id=uuid.UUID(admin_id), name="admin", api_key=admin_api_key, role="ADMIN"))
        await db.commit()
        break
    admin_headers = {"Authorization": f"TOKEN {admin_api_key}"}
    ticker = "MEMCOIN"
    instrument_body = {"ticker": ticker, "name": "Mem Coin"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post("/api/v1/admin/instrument", headers=admin_headers, json=instrument_body)
        # Пополняем баланс MEMCOIN второму (seller), USD первому (buyer)
        await ac.post("/api/v1/admin/balance/deposit", headers=admin_headers, json={
            "user_id": id2, "ticker": ticker, "amount": 10  # user_id как строка!
        })
        await ac.post("/api/v1/admin/balance/deposit", headers=admin_headers, json={
            "user_id": id1, "ticker": "RUB", "amount": 500
        })

    # --- Проверка начальных балансов ---
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/balance", headers=headers1)
        assert resp.json().get("RUB", 0) == 500
        resp = await ac.get("/api/v1/balance", headers=headers2)
        assert resp.json().get(ticker, 0) == 10

    # --- 1. Первый пользователь (BUYER) выставляет лимитный BUY ордер ---
    order_body_buy = {
        "direction": "BUY",
        "ticker": ticker,
        "qty": 5,
        "price": 20
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/v1/order", headers=headers1, json=order_body_buy)
        assert resp.status_code == 200
        order_id_buy = resp.json()["order_id"]

    # --- 2. Второй пользователь (SELLER) выставляет лимитный SELL ордер по той же цене ---
    order_body_sell = {
        "direction": "SELL",
        "ticker": ticker,
        "qty": 5,
        "price": 20
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/v1/order", headers=headers2, json=order_body_sell)
        assert resp.status_code == 200
        order_id_sell = resp.json()["order_id"]

    # --- После этого оба ордера должны исполниться (matching engine)! ---
    # Проверяем статусы ордеров
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/order/{order_id_buy}", headers=headers1)
        assert resp.status_code == 200
        buy_order = resp.json()
        assert buy_order["status"] == "EXECUTED"
        assert buy_order["filled"] == 5
        resp = await ac.get(f"/api/v1/order/{order_id_sell}", headers=headers2)
        assert resp.status_code == 200
        sell_order = resp.json()
        assert sell_order["status"] == "EXECUTED"
        assert sell_order["filled"] == 5

    # --- Проверяем обновлённые балансы ---
    # Покупатель: MEMCOIN +5, USD -100
    # Продавец: MEMCOIN -5, USD +100
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        b1 = await ac.get("/api/v1/balance", headers=headers1)
        b2 = await ac.get("/api/v1/balance", headers=headers2)
        bal1 = b1.json()
        bal2 = b2.json()
        assert bal1.get(ticker, 0) == 5
        assert bal1.get("RUB", 0) == 400
        assert bal2.get(ticker, 0) == 5
        assert bal2.get("RUB", 0) == 100

    # --- Проверяем, что сделка записана в истории ---
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/public/transactions/{ticker}?limit=1")
        tx = resp.json()[0]
        assert tx["ticker"] == ticker
        assert tx["amount"] == 5
        assert tx["price"] == 20
