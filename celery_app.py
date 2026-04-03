"""
Little Lines — Celery Configuration
Async task queue for heavy AI generation workloads
"""
import os
import sys
import ssl

# Ensure source directory is in Python path (fixes Render worker imports)
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Upstash requires SSL — Celery needs broker_use_ssl config
from celery import Celery

celery_app = Celery(
    'little_lines',
    broker=redis_url,
    backend=redis_url,
    include=['tasks']
)

# SSL config for Upstash (rediss:// URLs)
if redis_url.startswith('rediss://'):
    celery_app.conf.broker_use_ssl = {
        'ssl_cert_reqs': ssl.CERT_NONE
    }
    celery_app.conf.redis_backend_use_ssl = {
        'ssl_cert_reqs': ssl.CERT_NONE
    }

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    task_track_started=True,
    task_time_limit=600,       # 10 min hard limit per task
    task_soft_time_limit=540,  # 9 min soft limit
    worker_prefetch_multiplier=1,  # One task at a time per worker
    result_expires=3600,           # Results expire after 1 hour
    # Two-queue system: fast (colouring pages, reveals) and slow (stories, packs)
    task_default_queue='fast',
    task_routes={
        'tasks.generate_colouring_page_task': {'queue': 'fast'},
        'tasks.extract_and_reveal_task': {'queue': 'fast'},
        'tasks.character_reveal_flow_task': {'queue': 'fast'},
        'tasks.generate_full_story_task': {'queue': 'slow'},
        'tasks.generate_storybook_pdf_task': {'queue': 'slow'},
        'tasks.generate_pack_task': {'queue': 'slow'},
    },
)
