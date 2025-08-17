"""
Celery application configuration for alignment workers.
"""

import os
from celery import Celery
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Celery configuration
celery_app = Celery(
    'alignment_workers',
    broker=os.getenv('CELERY_BROKER_URL'),
    backend='rpc://',  # Use RPC backend for results
    include=['workers.tasks']  # Include task modules
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Task routing configuration
celery_app.conf.task_routes = {
    'workers.tasks.ping_task': {'queue': 'default'},
    'workers.tasks.process_alignment_task': {'queue': 'alignment'},
}

if __name__ == '__main__':
    celery_app.start()
