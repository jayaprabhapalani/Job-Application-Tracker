import json
import ssl
from aiokafka import AIOKafkaProducer
from app.config import settings

_producer: AIOKafkaProducer | None = None


def _get_producer_kwargs():
    kwargs = {"bootstrap_servers": settings.KAFKA_BOOTSTRAP_SERVERS}
    if getattr(settings, "KAFKA_SECURITY_PROTOCOL", "PLAINTEXT").upper() == "SASL_SSL":
        context = ssl.create_default_context()
        kwargs.update({
            "security_protocol": "SASL_SSL",
            "sasl_mechanism": settings.KAFKA_SASL_MECHANISM,
            "sasl_plain_username": settings.KAFKA_SASL_USERNAME,
            "sasl_plain_password": settings.KAFKA_SASL_PASSWORD,
            "ssl_context": context,
        })
    return kwargs


async def start_producer():
    global _producer
    _producer = AIOKafkaProducer(**_get_producer_kwargs())
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
