import json
from aiokafka import AIOKafkaProducer
from app.config import settings

_producer: AIOKafkaProducer | None = None


async def start_producer():
    global _producer
    _producer = AIOKafkaProducer(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)
    await _producer.start()


async def stop_producer():
    if _producer:
        await _producer.stop()


async def publish_event(topic: str, key: str, value: dict):
    if _producer is None:
        raise RuntimeError("Kafka producer not initialized. Call start_producer() on startup.")
    await _producer.send_and_wait(
        topic,
        key=key.encode(),
        value=json.dumps(value).encode(),
    )
