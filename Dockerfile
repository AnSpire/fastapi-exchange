# ---- 1. Билд-зависимости ----
FROM python:3.13-slim AS builder

WORKDIR /app

# Установим зависимости для сборки psycopg2 и других пакетов
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Скопируем зависимости
COPY pyproject.toml uv.lock ./

# Установим uv
RUN pip install uv

# Установим зависимости в отдельное окружение
RUN uv sync --frozen

# ---- 2. Финальный образ ----
FROM python:3.13-slim

WORKDIR /app

# Скопируем окружение из builder
COPY --from=builder /app/.venv /app/.venv

# Используем .venv как интерпретатор по умолчанию
ENV PATH="/app/.venv/bin:$PATH"

# Копируем всё приложение
COPY . .

# Укажем переменные окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Экспонируем порт
EXPOSE 8000

# Запуск через uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
