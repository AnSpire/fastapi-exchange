import pytest
import httpx
import uuid

BASE_URL = "http://localhost:8000"
ADMIN_API_KEY = "key-43408538-40c4-4f39-9277-581ee03b4cdb"
HEADERS_ADMIN = {"Authorization": f"TOKEN {ADMIN_API_KEY}"}

INSTRUMENT = "MEMCOIN"
QUOTE = "RUB"

@pytest.mark.asyncio
async def test_memcoin_order_matching_with_user_deletion():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # --- Создать инструмент MEMCOIN ---
        await client.post(
            "/api/v1/admin/instrument",
            json={"name": "Mem Coin", "ticker": INSTRUMENT},
            headers=HEADERS_ADMIN
        )

        # --- Регистрация продавцов и депозит MEMCOIN ---
        sellers = []
        for price in [90, 95]:
            name = f"Seller_{uuid.uuid4().hex[:8]}"
            r = await client.post("/api/v1/public/register", json={"name": name})
            assert r.status_code == 200, f"Seller reg failed: {r.text}"
            user = r.json()
            sellers.append({
                "id": user["id"],
                "api_key": user["api_key"],
                "price": price
            })
            # Депозит MEMCOIN для продажи
            await client.post(
                "/api/v1/admin/balance/deposit",
                json={"user_id": user["id"], "ticker": INSTRUMENT, "amount": 100},
                headers=HEADERS_ADMIN
            )

        # --- Регистрация покупателя и депозит RUB ---
        r = await client.post("/api/v1/public/register", json={"name": f"Buyer_{uuid.uuid4().hex[:8]}"})
        assert r.status_code == 200, f"Buyer reg failed: {r.text}"
        buyer = r.json()
        buyer_headers = {"Authorization": f"TOKEN {buyer['api_key']}"}
        # Депозит RUB для покупателя
        await client.post(
            "/api/v1/admin/balance/deposit",
            json={"user_id": buyer["id"], "ticker": QUOTE, "amount": 10000},
            headers=HEADERS_ADMIN
        )

        # --- Продавцы размещают заявки на продажу MEMCOIN ---
        orders_sell = []
        qty_per_seller = 10
        for seller in sellers:
            headers = {"Authorization": f"TOKEN {seller['api_key']}"}
            order_body = {
                "direction": "SELL",
                "ticker": INSTRUMENT,
                "qty": qty_per_seller,
                "price": seller["price"]
            }
            r = await client.post("/api/v1/order", json=order_body, headers=headers)
            assert r.status_code == 200, f"Seller order failed: {r.text}"
            orders_sell.append({
                "id": r.json()["order_id"],
                "price": seller["price"],
                "user_id": seller["id"]
            })

        # --- Покупатель размещает заявку на покупку MEMCOIN ---
        order_buy_body = {
            "direction": "BUY",
            "ticker": INSTRUMENT,
            "qty": 20,
            "price": 100  # Покупает обе заявки
        }
        for i, order in enumerate(orders_sell):
            print(f"Created SELL order: id={order['id']}, price={order['price']}, user={order['user_id']}")

        r = await client.post("/api/v1/order", json=order_buy_body, headers=buyer_headers)
        assert r.status_code == 200, f"Buyer order failed: {r.text}"
        buy_order_id = r.json()["order_id"]

        # --- Проверяем историю сделок ---
        r = await client.get(f"/api/v1/public/transactions/{INSTRUMENT}")
        print("ALL transactions:", r.json())
        assert r.status_code == 200, f"Transactions fetch failed: {r.text}"
        transactions = r.json()
        relevant = [tx for tx in transactions if tx["price"] in [90, 95] and tx["amount"] == qty_per_seller]
        relevant_sorted = sorted(relevant, key=lambda tx: tx["timestamp"])
        assert len(relevant_sorted) >= 2, f"Expected at least 2 matched trades, got: {relevant_sorted}"
        assert relevant_sorted[0]["price"] == 90, f"First match should be at price 90, got: {relevant_sorted[0]['price']}"
        assert relevant_sorted[1]["price"] == 95, f"Second match should be at price 95, got: {relevant_sorted[1]['price']}"

        # --- Проверяем статусы ордеров продавцов ---
        for i, order in enumerate(orders_sell):
            seller_headers = {"Authorization": f"TOKEN {sellers[i]['api_key']}"}
            r = await client.get(f"/api/v1/order/{order['id']}", headers=seller_headers)
            assert r.status_code == 200
            status = r.json().get("status")
            assert status == "EXECUTED" or status == "PARTIALLY_EXECUTED", f"Order {order['id']} not executed!"

        # --- Проверяем остаток заявки на покупку ---
        r = await client.get(f"/api/v1/order/{buy_order_id}", headers=buyer_headers)
        assert r.status_code == 200
        order_data = r.json()
        assert order_data["body"]["qty"] == 20
        assert order_data.get("filled", 0) == 20

        # --- Проверяем балансы продавцов ---
        for i, seller in enumerate(sellers):
            headers = {"Authorization": f"TOKEN {seller['api_key']}"}
            r = await client.get("/api/v1/balance", headers=headers)
            assert r.status_code == 200
            bal = r.json()
            assert bal.get(INSTRUMENT, 0) <= 100 - qty_per_seller
            assert bal.get(QUOTE, 0) >= sellers[i]["price"] * qty_per_seller

        # --- Удаляем продавцов (через админский эндпоинт) ---
        for seller in sellers:
            r = await client.delete(
                f"/api/v1/admin/user/{seller['id']}",
                headers=HEADERS_ADMIN
            )
            assert r.status_code == 200, f"Admin delete user failed: {r.text}"

        # --- Удаляем покупателя ---
        r = await client.delete(
            f"/api/v1/admin/user/{buyer['id']}",
            headers=HEADERS_ADMIN
        )
        assert r.status_code == 200, f"Admin delete user failed: {r.text}"

        # --- Проверяем, что все ордеры удалённых пользователей имеют статус CANCELED ---
        # (сначала продавцы)
        # for seller in sellers:
        #     # Получить список всех ордеров продавца (как админ)
        #     r = await client.get("/api/v1/order", headers={"Authorization": f"TOKEN {seller['api_key']}"})
        #     assert r.status_code == 200
        #     for order in r.json():
        #         assert order["status"] == "CANCELLED", (
        #             f"Order {order['id']} of deleted user {seller['id']} has status {order['status']}!"
        #         )
        #
        # # (покупатель)
        # r = await client.get("/api/v1/order", headers={"Authorization": f"TOKEN {buyer['api_key']}"})
        # assert r.status_code == 200
        # for order in r.json():
        #     assert order["status"] == "CANCELLED", (
        #         f"Order {order['id']} of deleted user {buyer['id']} has status {order['status']}!"
        #     )

