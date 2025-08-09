# Руководство по миграции на доменную архитектуру

## Быстрый старт

### Запуск приложения
```bash
# Активация виртуальной среды
source venv/bin/activate

# Запуск сервера
python run.py
# или
uvicorn app.main:app --reload
```

### Проверка работоспособности
```bash
# Проверка импортов
python -c "from app.main import app; print('✅ OK')"

# Проверка API
curl http://localhost:8000/health
```

## Изменения в импортах

### Рекомендуемые импорты (новые)

```python
# Модели
from app.domains.alignment.models import AlignmentQueue, AlignmentStatus
from app.domains.models.models import MFAModel, Language, ModelType

# Схемы
from app.domains.alignment.schemas import AlignmentQueueResponse
from app.domains.models.schemas import MFAModelResponse

# CRUD
from app.domains.alignment.crud import create_alignment_task
from app.domains.models.crud import get_mfa_models

# Сервисы
from app.domains.models.services.mfa_service import MFAModelService
```

### Совместимые импорты (старые, все еще работают)

```python
# Все старые импорты продолжают работать
from app.models import AlignmentQueue, MFAModel
from app.schemas import AlignmentQueueResponse
from app.crud import create_alignment_task
```

## Что изменилось

### ✅ Что работает как раньше
- Все API endpoints остались теми же
- Все существующие импорты работают
- База данных не изменилась
- Конфигурация не изменилась

### 🔄 Что улучшилось
- Код организован по доменам
- Устранены циклические зависимости
- Легче добавлять новые функции
- Лучшая читаемость кода

### 📁 Новая структура файлов
```
app/domains/
├── alignment/          # Домен выравнивания
│   ├── models.py      # AlignmentQueue, AlignmentStatus
│   ├── schemas.py     # API схемы
│   ├── crud.py        # CRUD операции
│   └── router.py      # API endpoints
└── models/            # Домен MFA моделей
    ├── models.py      # MFAModel, Language
    ├── schemas.py     # API схемы
    ├── crud.py        # CRUD операции
    ├── router.py      # API endpoints
    └── services/      # Бизнес-логика
```

## Рекомендации

### Для нового кода
- Используйте импорты из доменов
- Следуйте структуре доменов при добавлении функций

### Для существующего кода
- Можете оставить старые импорты
- Постепенно мигрируйте при внесении изменений

### Для тестов
- Обновите импорты для лучшей читаемости
- Тестируйте домены независимо

## Примеры использования

### Создание задачи выравнивания
```python
from app.domains.alignment.crud import create_alignment_task
from app.domains.alignment.schemas import AlignmentQueueCreate, ModelParameter

# Создание задачи
task_data = AlignmentQueueCreate(
    original_audio_filename="audio.wav",
    original_text_filename="text.txt",
    acoustic_model=ModelParameter(name="english_us_arpa", version="2.2.0"),
    dictionary_model=ModelParameter(name="english_us_arpa", version="2.2.0")
)

task = create_alignment_task(db, task_data, "/path/to/audio.wav", "/path/to/text.txt")
```

### Работа с MFA моделями
```python
from app.domains.models.crud import get_mfa_models
from app.domains.models.services.mfa_service import MFAModelService

# Получение моделей
models = get_mfa_models(db, language_code="en")

# Обновление моделей
service = MFAModelService()
updated_count, lang_count = await service.update_models_from_github(db)
```

## Поддержка

Если возникли проблемы:
1. Проверьте, что используете правильные импорты
2. Убедитесь, что виртуальная среда активирована
3. Проверьте логи на наличие ошибок импорта
