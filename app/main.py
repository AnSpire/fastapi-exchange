# app/main.py

from fastapi import FastAPI
from app.api.v1.public import register
from app.api.v1 import me
from app.api.v1.public import instrument
from app.api.v1.admin import instrument as admin_instrument
from app.api.v1 import balance as balance_router
from app.api.v1 import order as order_router
from app.api.v1.public import orderbook  # если путь: app/api/v1/orderbook.py
from app.api.v1.public import transactions
from app.api.v1.admin import balance
from app.api.v1.admin import user
app = FastAPI(
    title="Toy Exchange",
    version="1.0.0"
)




# Подключаем роутеры — только те, которые есть в openapi.json!


app.include_router(user.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(balance.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(transactions.router, prefix="/api/v1/public", tags=["public"])
app.include_router(orderbook.router, prefix="/api/v1/public", tags=["public"])
app.include_router(order_router.router, prefix="/api/v1", tags=["order"])
app.include_router(register.router, prefix="/api/v1/public", tags=["public"])
app.include_router(me.router, prefix="/api/v1", tags=["user"])
app.include_router(instrument.router, prefix="/api/v1/public", tags=["public"])
app.include_router(admin_instrument.router, prefix="/api/v1/admin/instrument", tags=["admin"])
app.include_router(balance_router.router, prefix="/api/v1", tags=["balance"])
# Если нужно будет добавить другие роутеры (instrument, order и т.д.) — подключай их так же!
