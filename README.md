# Text-Audio Alignment API

FastAPI приложение для принудительного выравнивания текста и аудио файлов.

# Описание

Это REST API предоставляет функциональность для управления очередью задач выравнивания текста и аудио. Приложение позволяет:

- Загружать аудио файлы (MP3, WAV) и текстовые файлы (TXT)
- Управлять очередью задач выравнивания (CRUD операции)
- Отслеживать статус выполнения задач
- Получать результаты выравнивания

## Домены: практическое назначение

- __Каталог моделей__: модели выравнивания (acoustic, dictionary, g2p); можно получать список (с фильтрами) и запускать задачу на автоматическое обновление.
- __Языки__: справочник поддерживаемых языков (для каких языков есть модели).
- __Alignment__: создание и управление задачами на выравнивание; задачи ставятся в очередь.

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
│  ├─ models.py               # ORM models and enums (AlignmentStatus, ModelType)
│  ├─ schemas.py              # Pydantic request/response schemas
│  ├─ crud.py                 # DB CRUD operations and model validations
│  ├─ utils.py                # File upload helpers (dir, save, extensions)
│  ├─ routers/                # API routers
│  │  ├─ __init__.py
│  │  ├─ alignment.py         # Alignment queue endpoints (CRUD, validate models)
│  │  └─ models.py            # MFA models endpoints (listing, filter by language)
│  └─ services/               # Business logic services
│     ├─ __init__.py
│     ├─ mfa_service.py       # Service interface/abstraction
│     └─ local_mfa_service.py # Local MFA implementation
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

## Папка `app/`

- __`app/main.py`__
  - Создаёт экземпляр `FastAPI`, настраивает Swagger UI, подключает роутеры из `app.routers`.
  - Эндпоинты здоровья: `GET /`, `GET /health`.

- __`app/database.py`__
  - Инициализирует `SQLAlchemy` (`engine`, `SessionLocal`, `Base`).
  - Читает параметры из `.env` (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`).
  - Провайдер соединения `get_db()` для зависимостей FastAPI.

- __`app/models.py`__
  - ORM-модели:
    - `Language` — языки моделей.
    - `MFAModel` — модели MFA (поля: `name`, `model_type`, `version`, `variant`, `language_id`, `description`).
    - `AlignmentQueue` — задачи выравнивания (пути к файлам, выбранные модели, статус, ошибки, результат).
  - Энамы: `AlignmentStatus`, `ModelType`.

- __`app/schemas.py`__
  - Pydantic-схемы для запросов/ответов API (создание/обновление задач, модели, языки, параметры моделей и т.д.).

- __`app/crud.py`__
  - Логика доступа к БД (CRUD):
    - Задачи выравнивания: `create_alignment_task()`, `get/update/delete`, фильтрация по статусу.
    - Языки: создание, выборка, bulk-операции, «get or create».
    - Модели MFA: создание, bulk, выборки (в т.ч. по типу и языку), удаление, счётчики.
  - Валидации моделей: `validate_model_exists()`, `validate_models_same_language()` — проверка существования моделей и единства языка у acoustic/dictionary/g2p.

- __`app/utils.py`__
  - Работа с файлами загрузки: создание каталога `uploads/`, проверка расширений, сохранение файла с уникальным именем.

### Подпапка `app/routers/`

- __`app/routers/alignment.py`__
  - Эндпоинты для очереди выравнивания (CRUD, статус, создание задач с валидацией выбранных моделей).
  - Использует схемы из `app.schemas` и CRUD из `app.crud`.

- __`app/routers/models.py`__
  - Эндпоинты каталога моделей (`GET /models`, `GET /models/by-type/{model_type}` с фильтром по языку и пагинацией; массовые операции импорт/очистка по необходимости).

### Подпапка `app/services/`

- __`app/services/mfa_service.py`__
  - Абстракция/интерфейс сервиса выравнивания: базовые методы и контракты для реализации.

- __`app/services/local_mfa_service.py`__
  - Локальная реализация сервиса MFA (запуск локальных процессов/скриптов, управление путями, подготовка данных). Сейчас имеет низкое покрытие тестами — рекомендуется добавить тесты.

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

Запуск тестов:

```bash
source venv/bin/activate
venv/bin/python -m pytest
```

Запуск тестов с покрытием:

```bash
venv/bin/python -m pytest --cov=app
```

Запуск конкретного теста:

```bash
venv/bin/python -m pytest tests/test_alignment_endpoints.py::TestAlignmentEndpoints::test_create_alignment_task_success
```

# Лицензия

MIT License
