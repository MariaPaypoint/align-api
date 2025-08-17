#!/bin/bash
# Скрипт для запуска тестов в Docker окружении

echo "🐳 Настройка Docker окружения для тестов..."

# Убеждаемся что используется Docker конфигурация
cp .env.docker .env

# Запускаем все сервисы
echo "🚀 Запуск сервисов..."
docker compose up -d

# Ждем пока сервисы поднимутся
echo "⏳ Ожидание готовности сервисов..."
sleep 10

# Запускаем все тесты в контейнере
echo "🧪 Запуск всех тестов в Docker..."
docker compose exec api python -m pytest -v --tb=short

echo "✅ Docker тесты завершены!"
