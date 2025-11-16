FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Рабочая директория внутри контейнера
WORKDIR /app

# Системные зависимости (минимальный набор)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

# Ставим uv
RUN pip install --no-cache-dir uv

# Копируем файлы зависимостей
COPY pyproject.toml uv.lock ./

# Ставим зависимости из pyproject/uv.lock
RUN uv sync --no-dev --frozen

# Копируем весь проект
COPY . .

# Открываем порт
EXPOSE 8000

# Команда запуска (обычный dev-server)
CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]