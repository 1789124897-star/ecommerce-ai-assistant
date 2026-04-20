from celery import Celery
from celery.schedules import crontab
from kombu import Exchange, Queue

from app.core.config import settings


celery_app = Celery(
    "ecommerce_ai_assistant",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.task_queues = (
    Queue("analysis", Exchange("analysis"), routing_key="analysis"),
    Queue("strategy", Exchange("strategy"), routing_key="strategy"),
    Queue("image_gen", Exchange("image_gen"), routing_key="image_gen"),
)

celery_app.conf.task_routes = {
    "app.workers.tasks.analyze_product_task": {"queue": "analysis", "routing_key": "analysis"},
    "app.workers.tasks.generate_strategies_task": {"queue": "strategy", "routing_key": "strategy"},
    "app.workers.tasks.generate_main_images_task": {"queue": "image_gen", "routing_key": "image_gen"},
    "app.workers.tasks.generate_detail_images_task": {"queue": "image_gen", "routing_key": "image_gen"},
    "app.workers.tasks.system_heartbeat_task": {"queue": "analysis", "routing_key": "analysis"},
}

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.TASK_TIME_LIMIT,
    task_soft_time_limit=settings.TASK_SOFT_TIME_LIMIT,
    task_acks_late=settings.TASK_ACKS_LATE,
    task_reject_on_worker_lost=settings.TASK_REJECT_ON_WORKER_LOST,
    result_expires=settings.RESULT_EXPIRES,
    worker_prefetch_multiplier=settings.WORKER_PREFETCH_MULTIPLIER,
    task_default_retry_delay=settings.TASK_DEFAULT_RETRY_DELAY,
)

celery_app.conf.beat_schedule = {
    "system-heartbeat-every-10-minutes": {
        "task": "app.workers.tasks.system_heartbeat_task",
        "schedule": crontab(minute="*/10"),
    }
}

celery_app.autodiscover_tasks(["app.workers"])
