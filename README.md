# Text-Audio Alignment API

FastAPI приложение для принудительного выравнивания текста и аудио файлов.

## Описание

Это REST API предоставляет функциональность для управления очередью задач выравнивания текста и аудио. Приложение позволяет:

- Загружать аудио файлы (MP3, WAV) и текстовые файлы (TXT)
- Управлять очередью задач выравнивания (CRUD операции)
- Отслеживать статус выполнения задач
- Получать результаты выравнивания

## Требования

- Python 3.11+
- MySQL 5.7+
- pip

## Установка и запуск

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

## Запуск приложения

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

## API Документация

После запуска приложения документация API будет доступна по адресам:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Основные эндпоинты

### Создание задачи выравнивания

```http
POST /alignment/
Content-Type: multipart/form-data

Form data:
- audio_file: файл (MP3 или WAV)
- text_file: файл (TXT)
```

### Получение всех задач

```http
GET /alignment/?skip=0&limit=100
```

### Получение задачи по ID

```http
GET /alignment/{task_id}
```

### Обновление задачи

```http
PUT /alignment/{task_id}
Content-Type: application/json

{
  "status": "processing",
  "result_path": "/path/to/result.json",
  "error_message": "Error description"
}
```

### Удаление задачи

```http
DELETE /alignment/{task_id}
```

### Получение задач по статусу

```http
GET /alignment/status/{status}
```

Доступные статусы: `pending`, `processing`, `completed`, `failed`

## Структура проекта

```
align-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # Основное приложение FastAPI
│   ├── database.py          # Настройка подключения к БД
│   ├── models.py            # SQLAlchemy модели
│   ├── schemas.py           # Pydantic схемы
│   ├── crud.py              # CRUD операции
│   ├── utils.py             # Вспомогательные функции
│   └── routers/
│       ├── __init__.py
│       └── alignment.py     # Роутеры для эндпоинтов выравнивания
├── alembic/                 # Миграции базы данных
├── tests/                   # Тесты
├── uploads/                 # Папка для загруженных файлов
├── requirements.txt         # Зависимости Python
├── .env.sample             # Пример конфигурации
└── README.md               # Этот файл
```

## Тестирование

Запуск тестов:

```bash
source venv/bin/activate
pytest
```

Запуск тестов с покрытием:

```bash
pytest --cov=app
```

Запуск конкретного теста:

```bash
pytest tests/test_alignment_endpoints.py::TestAlignmentEndpoints::test_create_alignment_task_success
```

## Модели данных

### AlignmentQueue

Основная модель для хранения задач выравнивания:

- `id`: Уникальный идентификатор задачи
- `audio_file_path`: Путь к сохраненному аудио файлу
- `text_file_path`: Путь к сохраненному текстовому файлу
- `original_audio_filename`: Оригинальное имя аудио файла
- `original_text_filename`: Оригинальное имя текстового файла
- `status`: Статус задачи (pending, processing, completed, failed)
- `result_path`: Путь к файлу с результатами выравнивания
- `error_message`: Сообщение об ошибке (если есть)
- `created_at`: Время создания задачи
- `updated_at`: Время последнего обновления

## Разработка

### Создание новой миграции

```bash
alembic revision --autogenerate -m "Description of changes"
```

### Применение миграций

```bash
alembic upgrade head
```

### Откат миграций

```bash
alembic downgrade -1  # Откат на одну миграцию назад
```

## Лицензия

MIT License

## Контакты

Для вопросов и предложений обращайтесь к разработчикам проекта.
