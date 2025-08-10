# Text-Audio Alignment API

FastAPI приложение для принудительного выравнивания текста и аудио файлов.

# Описание

Это REST API предоставляет функциональность для управления очередью задач выравнивания текста и аудио. Приложение позволяет:

- Загружать аудио файлы (MP3, WAV) и текстовые файлы (TXT)
- Управлять очередью задач выравнивания (CRUD операции)
- Отслеживать статус выполнения задач
- Получать результаты выравнивания

## Доменно-ориентированная архитектура

Проект организован по принципам **Domain-Driven Design (DDD)** с четким разделением на домены:

### Домены системы:

- **Домен выравнивания (`alignment`)**: создание и управление задачами на выравнивание; задачи ставятся в очередь, отслеживается их статус и результаты.
- **Домен моделей (`models`)**: каталог моделей выравнивания (acoustic, dictionary, g2p); справочник поддерживаемых языков; можно получать список (с фильтрами) и запускать задачу на автоматическое обновление.

### Преимущества архитектуры:

- **🏗️ Четкое разделение ответственности** - каждый домен решает свои задачи
- **📦 Отсутствие циклических зависимостей** - чистая архитектура
- **🔧 Легкость поддержки** - изменения в одном домене не влияют на другой
- **📈 Масштабируемость** - простое добавление новых доменов
- **🧪 Тестируемость** - изолированное тестирование каждого домена

Подробные запросы и поля в Swagger UI.

# Установка и запуск

### Требования

- Python 3.12+
- MySQL 5.7+
- pip

### Установка

1. Создайте виртуальное окружение:
```bash
python3 -m venv venv
```

2. Активируйте окружение:
```bash
source venv/bin/activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Настройка базы данных

Скопируйте файл `.env.sample` в `.env` и настройте подключение к базе данных:

```bash
cp .env.sample .env
```

Отредактируйте `.env` файл:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=align
```

5. Выполнение миграций

```bash
# Применить миграции
alembic upgrade head
```

### Запуск приложения

Режим разработки

```bash
./run.sh
```

```bash
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Режим продакшена

```bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Приложение будет доступно по адресу: http://localhost:8000

# API Документация

После запуска приложения документация API будет доступна по адресам:

  - **Swagger UI**: http://localhost:8000/docs
  - **ReDoc**: http://localhost:8000/redoc


# Структура проекта

```sh
align/
├─ app/                       # Application package
│  ├─ __init__.py
│  ├─ main.py                 # FastAPI app initialization and routers include
│  ├─ database.py             # SQLAlchemy engine/session and get_db dependency
│  ├─ utils.py                # File upload helpers (dir, save, extensions)
│  └─ domains/                # Domain-driven architecture
│     ├─ __init__.py
│     ├─ alignment/           # Alignment domain
│     │  ├─ __init__.py
│     │  ├─ models.py         # ORM models (AlignmentQueue, AlignmentStatus)
│     │  ├─ schemas.py        # Pydantic schemas for alignment
│     │  ├─ crud.py           # CRUD operations for alignment
│     │  ├─ router.py         # API endpoints for alignment
│     │  └─ services/         # Alignment business logic (future)
│     └─ models/              # Models domain
│        ├─ __init__.py
│        ├─ models.py         # ORM models (MFAModel, Language, ModelType)
│        ├─ schemas.py        # Pydantic schemas for models
│        ├─ crud.py           # CRUD operations for models
│        ├─ router.py         # API endpoints for models
│        └─ services/         # Models business logic
│           ├─ __init__.py
│           ├─ mfa_service.py       # Service interface/abstraction
│           └─ local_mfa_service.py # Local MFA implementation
├─ alembic/                   # Database migrations
│  ├─ env.py                  # Alembic environment config
│  ├─ script.py.mako          # Alembic revision template
│  └─ versions/               # Auto/hand-written migration files
├─ tests/                     # Pytest test suite
├─ run.py                     # App runner script
├─ alembic.ini                # Alembic settings
├─ requirements.txt           # Python dependencies
├─ pytest.ini                 # Pytest configuration
├─ .env.sample                # Environment variables sample
└─ mfa-models/                # Local MFA models storage (optional)
```

## Доменно-ориентированная архитектура `app/domains/`

Проект организован по принципам Domain-Driven Design (DDD) с четким разделением на домены:

### Домены системы:

- **`alignment/`** - управление задачами выравнивания текста и аудио
- **`models/`** - каталог MFA моделей и поддерживаемых языков

Каждый домен содержит собственные модели, схемы, CRUD операции, роутеры и сервисы.

## Прочие ключевые элементы

- __`alembic/`__ и `alembic.ini` — миграции БД (скрипты, конфигурация).
- __`tests/`__ — тесты PyTest (endpoints, CRUD, сервисы, валидации, утилиты). Используют `pytest`, `pytest-asyncio`, `pytest-cov`.
- __`run.py`__ — скрипт для локального запуска приложения.
- __`requirements.txt`__ — список зависимостей (включая `pytest`, `pytest-asyncio`, `pytest-cov`).
- __`pytest.ini`__ — конфигурация PyTest.
- __`.env.sample`__ — пример настроек окружения.
- __`mfa-models/`__ — каталог с локальными моделями MFA (если используется).

# Разработка

### Миграции

Создание новой миграции:

```bash
alembic revision --autogenerate -m "Description of changes"
```

Применение миграций:

```bash
alembic upgrade head
```

### Тестирование

Проект имеет **100% покрытие тестами** (85/85 тестов проходят успешно).

Запуск всех тестов:

```bash
source venv/bin/activate
python -m pytest
```

Запуск тестов с отчетом о покрытии:

```bash
python -m pytest --cov=app
```

Запуск тестов с подробным выводом:

```bash
python -m pytest -v
```

Запуск конкретного теста:

```bash
python -m pytest tests/test_alignment_endpoints.py::TestAlignmentEndpoints::test_create_alignment_task_success
```

Запуск тестов конкретного домена:

```bash
# Тесты домена выравнивания
python -m pytest tests/test_alignment_endpoints.py tests/test_alignment_with_models.py

# Тесты домена моделей  
python -m pytest tests/test_models_endpoints.py tests/test_models_crud.py tests/test_mfa_service.py
```

### Структура тестов

Тесты организованы по доменам и функциональности:

- **`test_alignment_endpoints.py`** - тестирование API endpoints домена выравнивания
- **`test_alignment_with_models.py`** - интеграционные тесты выравнивания с моделями
- **`test_models_endpoints.py`** - тестирование API endpoints домена моделей
- **`test_models_crud.py`** - тестирование CRUD операций домена моделей
- **`test_mfa_service.py`** - тестирование сервисов MFA
- **`test_russian_mfa_models.py`** - специфичные тесты для русских моделей
- **`test_utils.py`** - тестирование утилит

# Лицензия

MIT License
