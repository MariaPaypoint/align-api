#!/usr/bin/env python3
"""
Тест для проверки изоляции задач пользователей
"""
import requests
import json
import os
import uuid

# В Docker используем имя сервиса, локально - localhost
# Определяем окружение по наличию Docker контейнера или переменной CI
def get_base_url():
    # Проверяем переменные окружения, которые указывают на Docker/CI окружение
    if (os.getenv('TESTING_ENV') or 
        os.getenv('CI') or 
        os.path.exists('/.dockerenv')):
        return "http://api:8000"
    return "http://localhost:8000"

BASE_URL = get_base_url()

def test_user_task_isolation():
    """Проверяем, что пользователи видят только свои задачи"""
    
    # Генерируем уникальные данные для каждого запуска
    test_id = str(uuid.uuid4())[:8]
    
    # Регистрируем двух пользователей
    user1_data = {
        "email": f"user1_{test_id}@test.com",
        "password": "testpass123",
        "username": f"user1_{test_id}"
    }
    
    user2_data = {
        "email": f"user2_{test_id}@test.com", 
        "password": "testpass123",
        "username": f"user2_{test_id}"
    }
    
    print("Регистрируем пользователей...")
    
    # Регистрация пользователя 1
    response = requests.post(f"{BASE_URL}/auth/register", json=user1_data)
    print(f"Регистрация user1: {response.status_code}")
    
    # Регистрация пользователя 2  
    response = requests.post(f"{BASE_URL}/auth/register", json=user2_data)
    print(f"Регистрация user2: {response.status_code}")
    
    # Авторизация пользователя 1
    login_data = {"username": user1_data["username"], "password": user1_data["password"]}
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print(f"Ошибка авторизации user1: {response.status_code} - {response.text}")
        return
        
    token1 = response.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}
    
    # Авторизация пользователя 2
    login_data = {"username": user2_data["username"], "password": user2_data["password"]}
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print(f"Ошибка авторизации user2: {response.status_code} - {response.text}")
        return
        
    token2 = response.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}
    
    print("Пользователи авторизованы успешно")
    
    # Проверяем списки задач (должны быть пустыми)
    response1 = requests.get(f"{BASE_URL}/alignment/", headers=headers1)
    response2 = requests.get(f"{BASE_URL}/alignment/", headers=headers2)
    
    tasks1_before = len(response1.json()) if response1.status_code == 200 else 0
    tasks2_before = len(response2.json()) if response2.status_code == 200 else 0
    
    print(f"Задач у user1 до создания: {tasks1_before}")
    print(f"Задач у user2 до создания: {tasks2_before}")
    
    # Создаем тестовые файлы
    with open("/tmp/test_audio.wav", "w") as f:
        f.write("fake audio content")
    
    with open("/tmp/test_text.txt", "w") as f:
        f.write("Тестовый текст для выравнивания")
    
    # Пользователь 1 создает задачу
    files = {
        'audio_file': open('/tmp/test_audio.wav', 'rb'),
        'text_file': open('/tmp/test_text.txt', 'rb')
    }
    data = {
        'acoustic_model_name': 'russian_mfa',
        'acoustic_model_version': '3.1.0', 
        'dictionary_model_name': 'russian_mfa',
        'dictionary_model_version': '3.1.0'
    }
    
    response = requests.post(f"{BASE_URL}/alignment/", files=files, data=data, headers=headers1)
    print(f"Создание задачи user1: {response.status_code}")
    
    if response.status_code == 201:
        task_id = response.json()["id"]
        print(f"Создана задача с ID: {task_id}")
        
        # Проверяем списки задач после создания
        response1 = requests.get(f"{BASE_URL}/alignment/", headers=headers1)
        response2 = requests.get(f"{BASE_URL}/alignment/", headers=headers2)
        
        tasks1_after = len(response1.json()) if response1.status_code == 200 else 0
        tasks2_after = len(response2.json()) if response2.status_code == 200 else 0
        
        print(f"Задач у user1 после создания: {tasks1_after}")
        print(f"Задач у user2 после создания: {tasks2_after}")
        
        # Проверяем доступ к конкретной задаче
        response1_task = requests.get(f"{BASE_URL}/alignment/{task_id}", headers=headers1)
        response2_task = requests.get(f"{BASE_URL}/alignment/{task_id}", headers=headers2)
        
        print(f"Доступ user1 к своей задаче: {response1_task.status_code}")
        print(f"Доступ user2 к чужой задаче: {response2_task.status_code}")
        
        # Результат теста
        if (tasks1_after > tasks1_before and 
            tasks2_after == tasks2_before and
            response1_task.status_code == 200 and
            response2_task.status_code == 404):
            print("\n✅ ТЕСТ ПРОЙДЕН: Изоляция пользователей работает корректно!")
        else:
            print("\n❌ ТЕСТ НЕ ПРОЙДЕН: Проблемы с изоляцией пользователей")
    else:
        print(f"Ошибка создания задачи: {response.text}")

if __name__ == "__main__":
    test_user_task_isolation()
