import dramatiq
from dramatiq.middleware.asyncio import AsyncIO
from dramatiq.brokers.redis import RedisBroker

from googleapiclient.discovery import build

from src.mail import get_credentials, create_message
from src.config import Config

import logging

broker = RedisBroker(url=Config.REDIS_MQ_URL)
broker.add_middleware(AsyncIO())
dramatiq.set_broker(broker)

logger = logging.getLogger(__name__)

@dramatiq.actor
async def send_email(recipients: list[str], subject: str, body: str):
    logger.info("Task started")
    
    creds = get_credentials()
    service = build('gmail', 'v1', credentials=creds)

    message = create_message(recipients=recipients, subject=subject, body=body)

    service.users().messages().send(userId="me", body=message).execute()

    logger.info("Task completed")

