from celery import Celery
from ..config import settings
celery_app = Celery("lumetrix", broker=settings.REDIS_URL, backend=settings.REDIS_URL)
celery_app.conf.task_track_started = True

@celery_app.task
def send_campaign_task(campaign_id: int):
    from ..emailing.send_service import send_campaign
    send_campaign(campaign_id)
