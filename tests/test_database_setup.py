"""
Универсальная настройка тестовой базы данных для локального окружения
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.database import Base

# Импортируем все модели для создания таблиц
from api.domains.users.models import User, SubscriptionType, FileStorageMetadata
from api.domains.models.models import Language, MFAModel
from api.domains.alignment.models import AlignmentQueue

def get_test_engine():
    """Создает engine для тестирования"""
    # Всегда используем SQLite для тестов
    test_db_url = os.getenv('TEST_DATABASE_URL', 'sqlite:///./test.db')
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    return engine

def setup_test_database(engine):
    """Создает все таблицы для тестирования"""
    # Удаляем старые таблицы и создаем новые
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
def get_test_session_factory(engine):
    """Создает фабрику сессий для тестирования"""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)
