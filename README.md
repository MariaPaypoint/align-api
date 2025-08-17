# Text-Audio Alignment API

Распределенная система для принудительного выравнивания текста и аудио с использованием Montreal Forced Alignment (MFA).

## Архитектура

Подробная архитектура описана в файле `docs/architecture.md`. 

Система включает:
- **API** (FastAPI) - REST API для управления задачами
- **Workers** (Celery) - асинхронная обработка задач
- **Message Broker** (RabbitMQ) - очередь сообщений
- **Database** (MySQL) - хранение метаданных
- **File Storage** (MinIO) - объектное хранилище
- **Monitoring** (OpenObserve + Flower) - логирование и мониторинг

## Шаг 1: Базовая инфраструктура ✅

### Требования
- Docker и Docker Compose
- Python 3.12+

### Запуск инфраструктуры

```bash
docker-compose up -d
```

### Доступные сервисы

После запуска `docker-compose up -d` будут доступны:

- **FastAPI** (в разработке): http://localhost:8000
- **RabbitMQ Management**: http://localhost:15672 (admin:admin123)
- **MinIO Console**: http://localhost:9001 (minioadmin:minioadmin)  
- **OpenObserve**: http://localhost:5080 (admin@example.com:Complexpass#123)
- **Flower (Celery UI)**: http://localhost:5555
- **MySQL**: localhost:3306

### Тестирование Celery

```bash
# 1. Запуск Celery worker в отдельном терминале
source venv/bin/activate
python start_worker.py

# 2. Тестирование ping задачи в Python консоли
python -c "
from workers.tasks import ping_task
result = ping_task.delay('test message')
print('Task ID:', result.id)
print('Result:', result.get(timeout=10))
"
```

### Тестирование инфраструктуры

```bash
# Запуск тестов инфраструктуры
source venv/bin/activate
python -m pytest tests/test_infrastructure.py -v

# Тесты включают:
# - test_rabbitmq_connection()
# - test_redis_connection() 
# - test_minio_connection()
# - test_file_upload_download()
# - test_celery_ping_task()
```

### Остановка сервисов

```bash
# Остановка всех контейнеров
docker-compose down

# Очистка томов (ВНИМАНИЕ: удалит все данные)
docker-compose down -v
```

## Разработка

### Миграции (через Docker)
```bash
# Применение миграций в контейнере
docker-compose exec api python -m alembic upgrade head

# Создание новой миграции
docker-compose exec api python -m alembic revision --autogenerate -m "Description"
```

### Тестирование

#### Быстрый запуск тестов

**Локальное тестирование (рекомендуется для разработки):**
```bash
# Запуск основных тестов без Docker
./test_local.sh
```

**Полное тестирование в Docker:**
```bash
# Запуск всех тестов с инфраструктурой
./test_docker.sh
```

#### Ручное тестирование

**Локальное окружение:**
```bash
# Настройка локального окружения
cp .env.local .env
source venv/bin/activate
venv/bin/python -m pip install -r requirements.txt

# Запуск
venv/bin/python -m pytest --cov=api
```

**Docker окружение:**
```bash
# Запуск Docker окружения
docker compose up -d

# Запуск всех тестов в контейнере
docker compose exec api python -m pytest --cov=api
```

#### Конфигурационные файлы

- `.env` - настройки для локального окружения (SQLite, localhost)
- `.env.docker` - настройки для Docker окружения (MySQL, service names)

### API Документация

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
