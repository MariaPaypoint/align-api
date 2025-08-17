#!/usr/bin/env python3
"""
Script to start Celery worker.
"""

import os
import sys
from workers.celery_app import celery_app

if __name__ == '__main__':
    # Set environment variable for development
    os.environ.setdefault('PYTHONPATH', os.path.dirname(os.path.abspath(__file__)))
    
    # Start worker
    celery_app.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=4',
        '--queues=default,alignment'
    ])
