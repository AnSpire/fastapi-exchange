import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.base import Base  # или правильный import
from app.models.user import User  # путь до твоей модели
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import uuid

# Конфиг для тестовой базы, если требуется
# SQLALCHEMY_TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"  # пример для SQLite

# Создаём тестовый engine и session, если не используешь Depends(get_db)
# engine = create_async_engine(SQLALCHEMY_TEST_DATABASE_URL, future=True)
# TestingSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

@pytest.mark.asyncio
async def test_register_user():
    # Очистка пользователей с именем 'testuser'
    from app.dependencies import get_db  # если get_db возвращает AsyncSession

    # Открываем сессию через Depends(get_db) или через ручной engine
    async for db in get_db():
        await db.execute(
            User.__table__.delete().where(User.name == "testuser")
        )
        await db.commit()
        break

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.post("/api/v1/public/register", json={
            "name": "testuser"
        })
        assert resp.status_code == 200

        user = resp.json()

        assert user["name"] == "testuser"
        assert user["role"] == "USER"

        # Проверка, что id это UUID4 (строго)
        try:
            uuid_obj = uuid.UUID(user["id"])
        except Exception:
            assert False, "id is not a valid uuid"
        assert uuid_obj.version == 4, "id is not a uuid4"
        assert str(uuid_obj) == user["id"]

        # Проверка api_key
        assert user["api_key"].startswith("key-")
        uuid_part = user["api_key"][4:]
        try:
            api_key_uuid = uuid.UUID(uuid_part)
        except Exception:
            assert False, "api_key does not contain a valid uuid"
        assert api_key_uuid.version == 4, "api_key does not contain a uuid4"

        # Проверка наличия всех обязательных полей
        assert set(user.keys()) == {"id", "name", "role", "api_key"}
