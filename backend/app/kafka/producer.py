import json
import os
import ssl
from aiokafka import AIOKafkaProducer
from app.config import settings

_producer: AIOKafkaProducer | None = None


def _build_ssl_context():
    context = ssl.create_default_context()
    ca_cert = getattr(settings, "KAFKA_SSL_CA_CERT", None)
    if ca_cert:
        if os.path.exists(ca_cert):
            context.load_verify_locations(cafile=ca_cert)
        else:
            context.load_verify_locations(cadata=ca_cert)
    return context


def _get_producer_kwargs():
    kwargs = {"bootstrap_servers": settings.KAFKA_BOOTSTRAP_SERVERS}
    protocol = getattr(settings, "KAFKA_SECURITY_PROTOCOL", "PLAINTEXT").upper()
    if protocol == "SASL_SSL":
        kwargs.update({
            "security_protocol": "SASL_SSL",
            "sasl_mechanism": settings.KAFKA_SASL_MECHANISM,
            "sasl_plain_username": settings.KAFKA_SASL_USERNAME,
            "sasl_plain_password": settings.KAFKA_SASL_PASSWORD,
            "ssl_context": _build_ssl_context(),
        })
    elif protocol == "SSL":
        kwargs.update({
            "security_protocol": "SSL",
            "ssl_context": _build_ssl_context(),
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
