# Text-Audio Alignment API

FastAPI приложение для принудительного выравнивания текста и аудио файлов с использованием Montreal Forced Alignment (MFA).

## Возможности

- Загрузка аудио (MP3, WAV) и текстовых файлов
- Управление очередью задач выравнивания
- Отслеживание статуса выполнения
- Получение результатов выравнивания

## Архитектура

Описана в файле `docs/architecture.md`.

## Быстрый старт

### Требования
- Python 3.12+
- MySQL 8.0+

### Установка

```bash
# 1. Создание и активация виртуального окружения
python3 -m venv venv
source venv/bin/activate

# 2. Установка зависимостей
pip install -r requirements.txt

# 3. Настройка базы данных
cp .env.sample .env
# Отредактируйте .env файл

# 4. Применение миграций
python -m alembic upgrade head

# 5. Запуск приложения
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Приложение доступно по адресу: http://localhost:8000

## API Документация

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Разработка

### Миграции
```bash
# Создание новой миграции
source venv/bin/activate
python -m alembic revision --autogenerate -m "Description"

# Применение миграций
python -m alembic upgrade head
```

### Тестирование
```bash
# Запуск всех тестов
source venv/bin/activate
python -m pytest

# С покрытием кода
python -m pytest --cov=app
```
