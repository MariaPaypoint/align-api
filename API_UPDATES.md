# API Updates - Model Parameters

## Обзор изменений

Обновлены эндпоинты для работы с параметрами моделей MFA (Montreal Forced Alignment).

### Основные изменения:

1. **POST /alignment/** - добавлены обязательные параметры моделей
2. **GET /models/** - добавлен фильтр по языку
3. **GET /models/by-type/{model_type}** - добавлен фильтр по языку
4. Все CRUD операции для alignment обновлены для работы с параметрами моделей

## Обновленные эндпоинты

### POST /alignment/

Создание задачи выравнивания с параметрами моделей.

**Обязательные параметры:**
- `audio_file` (file) - аудио файл (MP3 или WAV)
- `text_file` (file) - текстовый файл (TXT)
- `acoustic_model_name` (form field) - название акустической модели
- `acoustic_model_version` (form field) - версия акустической модели
- `dictionary_model_name` (form field) - название словаря
- `dictionary_model_version` (form field) - версия словаря

**Необязательные параметры:**
- `g2p_model_name` (form field) - название G2P модели
- `g2p_model_version` (form field) - версия G2P модели

**Пример запроса с curl:**
```bash
curl -X POST "http://localhost:8000/alignment/" \
  -F "audio_file=@test_audio.wav" \
  -F "text_file=@test_text.txt" \
  -F "acoustic_model_name=english_us_arpa" \
  -F "acoustic_model_version=2.0.0" \
  -F "dictionary_model_name=english_us_arpa" \
  -F "dictionary_model_version=2.0.0" \
  -F "g2p_model_name=english_us_arpa" \
  -F "g2p_model_version=2.0.0"
```

**Валидация:**
- Проверяется существование всех указанных моделей в базе данных
- Проверяется, что все модели относятся к одному языку
- Проверяется корректность версий моделей

**Ответ:**
```json
{
  "id": 1,
  "original_audio_filename": "test_audio.wav",
  "original_text_filename": "test_text.txt",
  "audio_file_path": "/uploads/audio/test_audio.wav",
  "text_file_path": "/uploads/text/test_text.txt",
  "acoustic_model": {
    "name": "english_us_arpa",
    "version": "2.0.0"
  },
  "dictionary_model": {
    "name": "english_us_arpa", 
    "version": "2.0.0"
  },
  "g2p_model": {
    "name": "english_us_arpa",
    "version": "2.0.0"
  },
  "status": "pending",
  "result_path": null,
  "error_message": null,
  "created_at": "2025-08-04T01:00:00Z",
  "updated_at": "2025-08-04T01:00:00Z"
}
```

### GET /alignment/

Получение всех задач выравнивания с информацией о моделях.

**Параметры:**
- `skip` (int, optional) - количество записей для пропуска (default: 0)
- `limit` (int, optional) - максимальное количество записей (default: 100)

### GET /alignment/{task_id}

Получение конкретной задачи выравнивания с информацией о моделях.

### PUT /alignment/{task_id}

Обновление задачи выравнивания (статус, результат, ошибка).

### DELETE /alignment/{task_id}

Удаление задачи выравнивания.

### GET /alignment/status/{status}

Получение задач по статусу с информацией о моделях.

### GET /models/

Получение всех моделей MFA с фильтрацией по языку.

**Параметры:**
- `skip` (int, optional) - количество записей для пропуска (default: 0)
- `limit` (int, optional) - максимальное количество записей (default: 100)
- `language` (str, optional) - код языка для фильтрации (например: "english", "russian")

**Пример:**
```bash
curl "http://localhost:8000/models/?language=english&limit=10"
```

### GET /models/by-type/{model_type}

Получение моделей по типу с фильтрацией по языку.

**Параметры:**
- `model_type` (str) - тип модели: "acoustic", "dictionary", "g2p"
- `language` (str, optional) - код языка для фильтрации

**Пример:**
```bash
curl "http://localhost:8000/models/by-type/acoustic?language=english"
```

## Изменения в базе данных

### Таблица alignment_queue

Добавлены новые поля:
- `acoustic_model_name` (VARCHAR(255), NOT NULL) - название акустической модели
- `acoustic_model_version` (VARCHAR(50), NOT NULL) - версия акустической модели  
- `dictionary_name` (VARCHAR(255), NOT NULL) - название словаря
- `dictionary_version` (VARCHAR(50), NOT NULL) - версия словаря
- `g2p_model_name` (VARCHAR(255), NULL) - название G2P модели (необязательно)
- `g2p_model_version` (VARCHAR(50), NULL) - версия G2P модели (необязательно)

### Миграция

Для применения изменений в базе данных выполните:

```bash
cd /root/cep/align-api
alembic upgrade head
```

## Примеры использования

### Python с requests

```python
import requests

# Получение английских акустических моделей
response = requests.get("http://localhost:8000/models/by-type/acoustic?language=english")
models = response.json()

# Создание задачи выравнивания
files = {
    'audio_file': ('audio.wav', open('audio.wav', 'rb'), 'audio/wav'),
    'text_file': ('text.txt', open('text.txt', 'rb'), 'text/plain')
}

data = {
    'acoustic_model_name': 'english_us_arpa',
    'acoustic_model_version': '2.0.0',
    'dictionary_model_name': 'english_us_arpa',
    'dictionary_model_version': '2.0.0',
    'g2p_model_name': 'english_us_arpa',
    'g2p_model_version': '2.0.0'
}

response = requests.post("http://localhost:8000/alignment/", files=files, data=data)
task = response.json()
```

### JavaScript с fetch

```javascript
// Получение моделей
const modelsResponse = await fetch('http://localhost:8000/models/?language=english');
const models = await modelsResponse.json();

// Создание задачи выравнивания
const formData = new FormData();
formData.append('audio_file', audioFile);
formData.append('text_file', textFile);
formData.append('acoustic_model_name', 'english_us_arpa');
formData.append('acoustic_model_version', '2.0.0');
formData.append('dictionary_model_name', 'english_us_arpa');
formData.append('dictionary_model_version', '2.0.0');
formData.append('g2p_model_name', 'english_us_arpa');
formData.append('g2p_model_version', '2.0.0');

const response = await fetch('http://localhost:8000/alignment/', {
    method: 'POST',
    body: formData
});
const task = await response.json();
```

## Коды ошибок

- `400` - Неверные параметры (модель не найдена, модели разных языков, неверный формат JSON)
- `404` - Задача не найдена
- `500` - Внутренняя ошибка сервера

## Тестирование

Для тестирования API используйте файл `test_api_examples.py`:

```bash
cd /root/cep/align-api
python test_api_examples.py
```
