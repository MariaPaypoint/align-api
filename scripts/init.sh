#!/bin/bash
set -e

echo "Waiting for MySQL to be ready using Python..."
cd /app
python -c "
import time
import sys
from sqlalchemy import create_engine, text
import os

db_url = f'mysql+pymysql://{os.getenv(\"DB_USER\")}:{os.getenv(\"DB_PASSWORD\")}@{os.getenv(\"DB_HOST\")}:{os.getenv(\"DB_PORT\")}/{os.getenv(\"DB_NAME\")}'
max_attempts = 30

for attempt in range(max_attempts):
    try:
        engine = create_engine(db_url, connect_args={'connect_timeout': 5})
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        print('MySQL is ready!')
        break
    except Exception as e:
        if attempt < max_attempts - 1:
            print(f'MySQL not ready (attempt {attempt + 1}/{max_attempts}): {str(e)[:100]}')
            time.sleep(2)
        else:
            print('MySQL connection failed after all attempts')
            sys.exit(1)
"

echo "MySQL is up - running database migrations..."
python -m alembic upgrade heads

echo "Starting FastAPI application..."
exec uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
