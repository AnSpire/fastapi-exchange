# 1. Используем официальный образ python
FROM python:3.11

# 2. Устанавливаем рабочую директорию
WORKDIR /app

# 3. Копируем файлы проекта
COPY . .

# 4. Устанавливаем зависимости
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

# 5. Открываем порт (если нужно)
EXPOSE 8000

# 6. Запуск приложения через uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
