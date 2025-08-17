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

### API Документация

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
