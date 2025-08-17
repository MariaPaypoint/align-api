#!/bin/bash
# Скрипт для запуска тестов в локальном окружении

echo "🔧 Настройка локального окружения для тестов..."

# Копируем локальную конфигурацию
cp .env.local .env

# Устанавливаем зависимости
echo "📦 Установка зависимостей..."
source venv/bin/activate
pip install -r requirements.txt

# Запускаем только основные тесты (без инфраструктурных)
echo "🧪 Запуск основных тестов..."
python -m pytest tests/test_user_system.py \
                 tests/test_russian_mfa_models.py \
                 tests/test_user_request_success.py \
                 tests/test_alignment_with_models.py \
                 -v --tb=short

echo "✅ Локальные тесты завершены!"
