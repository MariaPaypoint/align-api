# Text-Audio Alignment API

Распределенная система для принудительного выравнивания текста и аудио с использованием Montreal Forced Alignment (MFA).

**⚠️ ВАЖНО: Проект работает ТОЛЬКО в Docker. Локальная разработка не поддерживается.**

## Архитектура

Подробная архитектура описана в файле `docs/architecture.md`. 

Система включает:
- **API** (FastAPI) - REST API для управления задачами
- **Workers** (Celery) - асинхронная обработка задач выравнивания
- **Message Broker** (RabbitMQ) - очередь сообщений
- **Database** (MySQL) - хранение метаданных
- **File Storage** (MinIO) - объектное хранилище
- **Monitoring** (OpenObserve + Flower) - логирование и мониторинг

## Требования

- Docker и Docker Compose
- Минимум 4GB RAM для всех сервисов

## Быстрый старт

### 1. Настройка переменных окружения

```bash
# Скопируйте пример конфигурации
cp .env.sample .env
# При необходимости отредактируйте .env файл
```

### 2. Запуск всех сервисов

```bash
docker compose up -d
```

### Доступные сервисы

После запуска `docker compose up -d` будут доступны:

- **FastAPI** (в разработке): http://localhost:8000
- **RabbitMQ Management**: http://localhost:15672 (admin:admin123)
- **MinIO Console**: http://localhost:9001 (minioadmin:minioadmin)  
- **OpenObserve**: http://localhost:5080 (admin@example.com:Complexpass#123)
- **Flower (Celery UI)**: http://localhost:5555
- **MySQL**: localhost:3306

### 3. Проверка работоспособности

```bash
# Проверка статуса всех сервисов
docker compose ps

# Просмотр логов
docker compose logs -f api
docker compose logs -f worker
```

## Разработка

### Тестирование

```bash
# Запуск всех тестов в Docker
./scripts/run_tests.sh

# Или запуск тестов вручную
docker compose run --rm tests

# Запуск конкретного теста
docker compose run --rm tests python -m pytest tests/test_infrastructure.py -v
```

### Миграции базы данных

```bash
# Применение миграций
docker compose exec api python -m alembic upgrade head

# Создание новой миграции
docker compose exec api python -m alembic revision --autogenerate -m "Description"
```

### Работа с Celery

```bash
# Просмотр статуса воркеров через Flower
# http://localhost:5555

# Выполнение тестовой задачи
docker compose exec api python -c "
from workers.tasks import ping_task
result = ping_task.delay('test message')
print('Task ID:', result.id)
print('Result:', result.get(timeout=10))
"
```

### Остановка сервисов

```bash
# Остановка всех контейнеров
docker compose down

# Очистка томов (ВНИМАНИЕ: удалит все данные)
docker compose down -v
```

## Полезные ссылки

После запуска `docker compose up -d` доступны:

- **API Swagger**: http://localhost:8000/docs
- **API ReDoc**: http://localhost:8000/redoc
- **RabbitMQ Management**: http://localhost:15672 (admin:admin123)
- **MinIO Console**: http://localhost:9001 (minioadmin:minioadmin)
- **OpenObserve**: http://localhost:5080 (admin@example.com:Complexpass#123)
- **Flower (Celery)**: http://localhost:5555

## Переменные окружения

Все настройки находятся в файле `.env`. 