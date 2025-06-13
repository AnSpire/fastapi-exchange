import pytest
from httpx import AsyncClient, ASGITransport
import uuid
from app.main import app
from app.models.user import User as UserORM
from app.db.session import async_session_maker

@pytest.mark.asyncio
async def test_admin_delete_user():
    async with async_session_maker() as session:
        await session.execute(UserORM.__table__.delete())
        await session.commit()
        admin = UserORM(
            id=str(uuid.uuid4()),
            name="admin",
            role="ADMIN",
            api_key="adminkey"
        )
        user = UserORM(
            id=str(uuid.uuid4()),
            name="user1",
            role="USER",
            api_key="userkey"
        )
        session.add_all([admin, user])
        await session.commit()

    admin_headers = {"Authorization": "TOKEN adminkey"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.delete(f"/api/v1/admin/user/{user.id}", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == user.id
        assert data["name"] == "user1"
        assert data["role"] == "USER"
        assert data["api_key"] == "userkey"

    # Проверить, что юзер удалён из базы
    async with async_session_maker() as session:
        deleted = await session.get(UserORM, user.id)
        assert deleted is None
