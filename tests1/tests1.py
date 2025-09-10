import pytest
import httpx

BASE_URL = "http://localhost:8000"
ADMIN_API_KEY = "adminkey-2ab7f720-5930-4a52-abe9-78b3f9053c27"
HEADERS_ADMIN = {"Authorization": f"TOKEN {ADMIN_API_KEY}"}
ADMIN_ID = "38cf2dab-ea82-4667-bbd2-eee1a7338d36"
TICKER = "RUB"
AMOUNT = 10000
PRICE = 100
QTY = 50

@pytest.mark.asyncio
async def test_basic_user_flow():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:

        # 1. Регистрация нового пользователя
        username = "TestUser8"
        r = await client.post("/api/v1/public/register", json={"name": username})
        assert r.status_code == 200, f"User creation failed: {r.text}"
        user = r.json()
        user_id = user["id"]
        user_api_key = user["api_key"]
        headers_user = {"Authorization": f"TOKEN {user_api_key}"}

        # 2. Создание тикера RUB (если он уже есть, это не вызовет ошибку)
        await client.post(
            "/api/v1/admin/instrument",
            json={"name": "Russian Ruble", "ticker": TICKER},
            headers=HEADERS_ADMIN
        )

        # 3. Пополнение баланса пользователя
        r = await client.post(
            "/api/v1/admin/balance/deposit",
            json={"user_id": user_id, "ticker": TICKER, "amount": AMOUNT},
            headers=HEADERS_ADMIN
        )
        assert r.status_code == 200, f"Deposit failed: {r.text}"

        # 4. Проверка баланса
        r = await client.get("/api/v1/balance", headers=headers_user)
        assert r.status_code == 200, f"Balance fetch failed: {r.text}"
        balance = r.json()
        assert balance.get(TICKER, 0) >= AMOUNT

        # 5. Размещение лимитного ордера на покупку
        order_body = {
            "direction": "BUY",
            "ticker": TICKER,
            "qty": QTY,
            "price": PRICE
        }
        r = await client.post("/api/v1/order", json=order_body, headers=headers_user)
        assert r.status_code == 200, f"Order creation failed: {r.text}"
        order_id = r.json()["order_id"]

        # 6. Получение информации об ордере
        r = await client.get(f"/api/v1/order/{order_id}", headers=headers_user)
        assert r.status_code == 200, f"Get order failed: {r.text}"
        order_data = r.json()
        assert order_data["id"] == order_id
        assert order_data["body"]["ticker"] == TICKER

        # 7. Получение истории сделок (может быть пусто, если ордер не исполнен)
        r = await client.get(f"/api/v1/public/transactions/{TICKER}")
        assert r.status_code == 200
        assert isinstance(r.json(), list)
