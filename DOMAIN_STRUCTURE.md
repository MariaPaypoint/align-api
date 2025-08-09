# Domain-Driven Architecture

Этот документ описывает новую доменную архитектуру проекта Text-Audio Alignment API.

## Структура проекта

```
app/
├── main.py                           # Основное приложение FastAPI
├── database.py                       # Конфигурация базы данных
├── utils.py                         # Общие утилиты
├── models.py                        # Совместимость: импорты из доменов
├── schemas.py                       # Совместимость: импорты из доменов  
├── crud.py                          # Совместимость: импорты из доменов
├── domains/                         # Доменная архитектура
│   ├── alignment/                   # Домен выравнивания
│   │   ├── models.py               # AlignmentQueue, AlignmentStatus
│   │   ├── schemas.py              # Pydantic схемы для alignment
│   │   ├── crud.py                 # CRUD операции для alignment
│   │   ├── router.py               # API endpoints (/alignment/*)
│   │   └── services/               # Сервисы домена alignment
│   └── models/                     # Домен MFA моделей
│       ├── models.py               # MFAModel, Language, ModelType
│       ├── schemas.py              # Pydantic схемы для models
│       ├── crud.py                 # CRUD операции для models
│       ├── router.py               # API endpoints (/models/*)
│       └── services/               # Сервисы домена models
│           ├── mfa_service.py      # Управление MFA моделями
│           └── local_mfa_service.py # Локальная работа с репозиторием
├── routers/                        # DEPRECATED: старые роутеры
└── services/                       # DEPRECATED: старые сервисы
```

## Домены

### 1. Alignment Domain (`app/domains/alignment/`)

**Ответственность**: Управление задачами выравнивания текста и аудио

**Компоненты**:
- `models.py`: SQLAlchemy модели (`AlignmentQueue`, `AlignmentStatus`)
- `schemas.py`: Pydantic схемы для API
- `crud.py`: CRUD операции для задач выравнивания
- `router.py`: API endpoints (`/alignment/*`)

**API Endpoints**:
- `POST /alignment/` - Создание задачи выравнивания
- `GET /alignment/` - Получение всех задач
- `GET /alignment/{task_id}` - Получение конкретной задачи
- `PUT /alignment/{task_id}` - Обновление задачи
- `DELETE /alignment/{task_id}` - Удаление задачи
- `GET /alignment/status/{status}` - Получение задач по статусу

### 2. Models Domain (`app/domains/models/`)

**Ответственность**: Управление MFA моделями и языками

**Компоненты**:
- `models.py`: SQLAlchemy модели (`MFAModel`, `Language`, `ModelType`)
- `schemas.py`: Pydantic схемы для API
- `crud.py`: CRUD операции для моделей и языков
- `router.py`: API endpoints (`/models/*`)
- `services/mfa_service.py`: Сервис управления моделями
- `services/local_mfa_service.py`: Локальная работа с репозиторием

**API Endpoints**:
- `GET /models/` - Получение всех MFA моделей
- `GET /models/by-type/{model_type}` - Получение моделей по типу
- `GET /models/languages` - Получение поддерживаемых языков
- `POST /models/update` - Обновление моделей из GitHub

## Преимущества новой архитектуры

### 🎯 Разделение ответственности
- Каждый домен содержит только свою бизнес-логику
- Четкие границы между различными областями функциональности
- Легче понять и поддерживать код

### 📦 Модульность
- Независимые домены можно разрабатывать параллельно
- Легче тестировать отдельные компоненты
- Возможность переиспользования кода

### 🔄 Масштабируемость
- Простое добавление новых доменов
- Легкое расширение существующих доменов
- Горизонтальное масштабирование команды

### 🧹 Чистота кода
- Устранение циклических зависимостей
- Более понятная структура импортов
- Следование принципам SOLID

## Обратная совместимость

Для обеспечения плавного перехода созданы файлы совместимости:

- `app/models.py` - импортирует модели из доменов
- `app/schemas.py` - импортирует схемы из доменов  
- `app/crud.py` - импортирует CRUD функции из доменов

Это позволяет существующему коду продолжать работать без изменений:

```python
# Старый способ (все еще работает)
from app.models import AlignmentQueue, MFAModel
from app.schemas import AlignmentQueueResponse
from app.crud import create_alignment_task

# Новый способ (рекомендуется)
from app.domains.alignment.models import AlignmentQueue
from app.domains.models.models import MFAModel
from app.domains.alignment.schemas import AlignmentQueueResponse
from app.domains.alignment.crud import create_alignment_task
```

## Миграция

### Для разработчиков

1. **Новый код**: используйте импорты из доменов
2. **Существующий код**: можете оставить старые импорты или постепенно мигрировать
3. **Новые домены**: создавайте в `app/domains/`

### Для тестов

Обновите импорты в тестах для использования новой структуры:

```python
# Вместо
from app.models import AlignmentQueue

# Используйте
from app.domains.alignment.models import AlignmentQueue
```

## Будущие улучшения

1. **Добавление новых доменов** (например, `notifications`, `analytics`)
2. **Разделение сервисов** на более мелкие компоненты
3. **Добавление событийной архитектуры** между доменами
4. **Внедрение паттерна Repository** для абстракции доступа к данным

## Заключение

Новая доменная архитектура обеспечивает:
- ✅ Лучшую организацию кода
- ✅ Упрощенное тестирование
- ✅ Легкую поддержку и развитие
- ✅ Масштабируемость команды
- ✅ Обратную совместимость
