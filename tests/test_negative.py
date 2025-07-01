import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
import uuid
from app.models.user import User
from app.dependencies import get_db
@pytest.mark.asyncio
async def test_edge_cases_api():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Регистрация с пустым body
        resp = await ac.post("/api/v1/public/register", json={})
        assert resp.status_code == 422  # missing required field

        # 2. Регистрация с лишним полем
        resp = await ac.post("/api/v1/public/register", json={"name": "edgeuser", "extra_field": "zzz"})
        assert resp.status_code == 422  # if pydantic config extra="forbid"

        # Зарегистрируем пользователя для остальных тестов
        resp = await ac.post("/api/v1/public/register", json={"name": "edgeuser2"})
        assert resp.status_code == 200
        user = resp.json()
        user_id = user["id"]
        api_key = user["api_key"]
        headers = {"Authorization": f"TOKEN {api_key}"}

        # 3. Попытка пополнить баланс с невалидным UUID
        # Создай админа заранее!
        admin_api_key = f"adminkey-{uuid.uuid4()}"
        admin_id = uuid.uuid4()
        async for db in get_db():
            db.add(User(id=admin_id, name="admininstr3", api_key=admin_api_key, role="ADMIN"))
            await db.commit()
            break
        admin_headers = {"Authorization": f"TOKEN {admin_api_key}"}

        # Теперь тестируй:
        deposit_body_bad_uuid = {
            "user_id": "not-a-uuid",
            "ticker": "MEMCOIN",
            "amount": 100
        }
        resp = await ac.post("/api/v1/admin/balance/deposit", headers=admin_headers, json=deposit_body_bad_uuid)
        assert resp.status_code == 422  # теперь будет правильная валидация uuid!

        # 4. Пополнение баланса с пустым body
        resp = await ac.post("/api/v1/admin/balance/deposit", headers=admin_headers, json={})
        assert resp.status_code == 422  # missing fields

        # 5. Пополнение баланса с лишним полем
        deposit_body = {
            "user_id": user_id,
            "ticker": "MEMCOIN",
            "amount": 100,
            "extra": 123
        }
        resp = await ac.post("/api/v1/admin/balance/deposit", headers=admin_headers, json=deposit_body)
        assert resp.status_code == 422

        # 6. Создание ордера с невалидным тикером
        order_body = {
            "direction": "BUY",
            "ticker": "mem!",  # невалидный тикер (маленькие буквы, спецсимвол)
            "qty": 1,
            "price": 10
        }
        resp = await ac.post("/api/v1/order", headers=headers, json=order_body)
        # Ожидается 422 или 404, если валидация строгая
        assert resp.status_code in (422, 404)

        # 7. Создание ордера с пустым body
        resp = await ac.post("/api/v1/order", headers=headers, json={})
        assert resp.status_code == 422

        # 8. Создание ордера с лишними полями
        order_body = {
            "direction": "BUY",
            "ticker": "MEMCOIN",
            "qty": 1,
            "price": 10,
            "extra": "zzz"
        }
        resp = await ac.post("/api/v1/order", headers=headers, json=order_body)
        assert resp.status_code == 422
