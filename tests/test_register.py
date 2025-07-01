import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.user import User
from app.dependencies import get_db
import uuid

@pytest.mark.asyncio
async def test_register_user():
    # Очистка пользователей с именем 'testuser'
    async for db in get_db():
        await db.execute(
            User.__table__.delete().where(User.name == "testuser")
        )
        await db.commit()
        break

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.post("/api/v1/public/register", json={"name": "testuser"})
        assert resp.status_code == 200, f"Unexpected status: {resp.status_code}, {resp.text}"

        user = resp.json()

        assert user["name"] == "testuser"
        assert user["role"] == "USER"

        # Проверка UUID4 для id и api_key — компактно
        for field, prefix in [("id", ""), ("api_key", "key-")]:
            value = user[field]
            if prefix:
                assert value.startswith(prefix), f"{field} has wrong prefix"
                value = value[len(prefix):]
            try:
                uuid_obj = uuid.UUID(value)
                assert uuid_obj.version == 4
            except Exception:
                pytest.fail(f"{field} is not a valid uuid4: {value}")

        # Проверка наличия всех обязательных полей
        assert set(user.keys()) == {"id", "name", "role", "api_key"}
