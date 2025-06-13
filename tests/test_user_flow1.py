import pytest
from httpx import AsyncClient, ASGITransport
import uuid
from app.main import app
from app.models.user import User
from app.models.instrument import Instrument
from app.db.session import async_session_maker

@pytest.mark.asyncio
async def test_full_user_flow():
    # Полная чистка пользователей и инструментов
    async with async_session_maker() as session:
        await session.execute(User.__table__.delete())
        await session.execute(Instrument.__table__.delete())
        await session.commit()
        # Создать админа
        admin_key = "adminkey"
        admin = User(
            id=str(uuid.uuid4()),
            name="admin",
            role="ADMIN",
            api_key=admin_key
        )
        session.add(admin)
        await session.commit()
        await session.refresh(admin)

    # === 1. РЕГИСТРАЦИЯ ПОЛЬЗОВАТЕЛЯ ===
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        reg_resp = await ac.post("/api/v1/public/register", json={"name": "user_test_123"})
        assert reg_resp.status_code == 200
        user_data = reg_resp.json()["user"]
        user_key = user_data["api_key"]
        user_headers = {"Authorization": f"TOKEN {user_key}"}

        # === 2. ПОЛУЧИТЬ СПИСОК ИНСТРУМЕНТОВ (или добавить свой, если их нет) ===
        instr_resp = await ac.get("/api/v1/public/instrument")
        assert instr_resp.status_code == 200
        instruments = instr_resp.json()

        ticker = None
        if instruments:
            ticker = instruments[0]["ticker"]
        else:
            # Добавить инструмент через админа
            instr_body = {"name": "Mem Coin", "ticker": "MEMCOIN"}
            admin_headers = {"Authorization": f"TOKEN {admin_key}"}
            add_instr_resp = await ac.post("/api/v1/admin/instrument", json=instr_body, headers=admin_headers)
            assert add_instr_resp.status_code == 200
            assert add_instr_resp.json()["success"] is True
            ticker = "MEMCOIN"

        # === 3. СОЗДАТЬ ЛИМИТНЫЙ ОРДЕР ===
        order_body = {
            "direction": "BUY",
            "ticker": ticker,
            "qty": 10,
            "price": 100
        }
        order_resp = await ac.post("/api/v1/order", json=order_body, headers=user_headers)
        assert order_resp.status_code == 200
        order_id = order_resp.json().get("order_id") or order_resp.json().get("id")
        assert order_id

        # === 4. ПОЛУЧИТЬ СПИСОК ОРДЕРОВ ===
        orders_resp = await ac.get("/api/v1/order", headers=user_headers)
        assert orders_resp.status_code == 200
        orders = orders_resp.json()
        assert any(
            order.get("id") == order_id or order.get("body", {}).get("ticker") == ticker
            for order in orders
        ), "Созданный ордер не найден в списке!"

        # === 5. ПРОВЕРИТЬ БАЛАНС ===
        balance_resp = await ac.get("/api/v1/balance", headers=user_headers)
        assert balance_resp.status_code == 200
        balances = balance_resp.json()
        assert isinstance(balances, dict)

    # Проверить, что инструмент действительно есть в базе (как в твоём примере)
    async with async_session_maker() as session:
        instrument = await session.get(Instrument, ticker)
        assert instrument is not None
