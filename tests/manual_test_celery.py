#!/usr/bin/env python3
"""
Скрипт для тестирования Celery задач.
"""

import sys
import os
import time

# Добавляем корневую папку проекта в PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ping_task():
    """Тестирует ping_task через Celery."""
    try:
        from workers.tasks import ping_task
        
        print("🚀 Запуск ping_task...")
        
        # Отправляем задачу в очередь
        result = ping_task.delay("test")
        
        print(f"✅ Задача отправлена. ID: {result.id}")
        print(f"📊 Статус: {result.status}")
        
        # Ждем результат (максимум 30 секунд)
        print("⏳ Ожидание результата...")
        try:
            task_result = result.get(timeout=30)
            print("🎉 Результат получен:")
            print(f"   - Task ID: {task_result.get('task_id', 'N/A')}")
            print(f"   - Message: {task_result.get('message', 'N/A')}")
            print(f"   - Timestamp: {task_result.get('timestamp', 'N/A')}")
            print(f"   - Worker ID: {task_result.get('worker_id', 'N/A')}")
            print(f"   - Status: {task_result.get('status', 'N/A')}")
            
        except Exception as e:
            print(f"❌ Ошибка при получении результата: {e}")
            print(f"📊 Финальный статус: {result.status}")
            raise
            
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("💡 Убедитесь, что Celery worker запущен и доступен")
        raise
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        raise

def main():
    """Основная функция."""
    print("🧪 Тестирование Celery ping_task")
    print("=" * 50)
    
    try:
        test_ping_task()
        print("=" * 50)
        print("✅ Тест успешно пройден!")
        print("💡 Проверьте Flower UI (http://localhost:5555) для просмотра задачи")
        return 0
    except Exception:
        print("=" * 50)
        print("❌ Тест не пройден")
        print("💡 Убедитесь, что:")
        print("   1. docker compose up запущен")
        print("   2. Celery worker запущен: python start_worker.py")
        print("   3. RabbitMQ доступен на localhost:5672")
        return 1

if __name__ == "__main__":
    sys.exit(main())
