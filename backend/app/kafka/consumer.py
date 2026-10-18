import asyncio
import json
import os
import ssl
from aiokafka import AIOKafkaConsumer
from app.config import settings
from app.kafka.topics import ANALYSIS_REQUESTS
from app.monitoring.logger import logger

_consumer: AIOKafkaConsumer | None = None


def _build_ssl_context():
    context = ssl.create_default_context()
    ca_cert = getattr(settings, "KAFKA_SSL_CA_CERT", None)
    if ca_cert and ca_cert.strip():
        if os.path.exists(ca_cert.strip()):
            context.load_verify_locations(cafile=ca_cert.strip())
        else:
            context.load_verify_locations(cadata=ca_cert.strip())
        return context

    # If no CA certificate provided, permit TLS without rejecting Aiven Project CA
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


def _get_consumer_kwargs():
    kwargs = {
        "bootstrap_servers": settings.KAFKA_BOOTSTRAP_SERVERS,
        "group_id": settings.KAFKA_CONSUMER_GROUP,
        "auto_offset_reset": "earliest",
    }
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


async def start_consumer():
    global _consumer
    _consumer = AIOKafkaConsumer(
        ANALYSIS_REQUESTS,
        **_get_consumer_kwargs(),
    )
    await _consumer.start()
    try:
        async for message in _consumer:
            try:
                job_data = json.loads(message.value.decode())
                from app.celery_app.tasks import run_agent_pipeline
                run_agent_pipeline.delay(job_data)
            except Exception as e:
                logger.error(f"Error processing Kafka message: {e}")
    finally:
        await _consumer.stop()


async def stop_consumer():
    global _consumer
    if _consumer:
        await _consumer.stop()
        _consumer = None
