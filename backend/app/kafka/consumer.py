import asyncio
import json
from aiokafka import AIOKafkaConsumer
from app.config import settings
from app.kafka.topics import ANALYSIS_REQUESTS

_consumer: AIOKafkaConsumer | None = None


async def start_consumer():
    global _consumer
    _consumer = AIOKafkaConsumer(
        ANALYSIS_REQUESTS,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=settings.KAFKA_CONSUMER_GROUP,
        auto_offset_reset="earliest",
    )
    await _consumer.start()
    try:
        async for message in _consumer:
            try:
                job_data = json.loads(message.value.decode())
                from app.celery_app.tasks import run_agent_pipeline
                run_agent_pipeline.delay(job_data)
            except Exception as e:
                print(f"Error processing Kafka message: {e}")
    finally:
        await _consumer.stop()


async def stop_consumer():
    global _consumer
    if _consumer:
        await _consumer.stop()
        _consumer = None
