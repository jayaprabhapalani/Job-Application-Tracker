import asyncio
from datetime import datetime, timedelta
from app.monitoring.logger import logger
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import time
from app.celery_app import celery_app
from app.config import settings
from app.agents.orchestrator import run_pipeline
from app.jobs.models import Application
from app.websocket.manager import manager
from app.monitoring.tracing import flush_langfuse
from app.monitoring.metrics import pipeline_total, pipeline_duration_seconds, active_pipelines


def _make_engine():
    return create_async_engine(settings.DATABASE_URL, pool_size=2, max_overflow=0)


@celery_app.task(name="app.celery_app.tasks.run_agent_pipeline")
def run_agent_pipeline(job_data: dict):
    job_id = job_data["job_id"]
    user_id = job_data.get("user_id", "")
    jd_text = job_data.get("jd_text", "")
    company = job_data.get("company", "")
    role = job_data.get("role", "")

    async def _run():
        engine = _make_engine()
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        try:
            async with session_factory() as db:
                await db.execute(
                    update(Application)
                    .where(Application.id == job_id)
                    .values(pipeline_status="running")
                )
                await db.commit()
            active_pipelines.inc()
            start = time.monotonic()
            try:
                await run_pipeline(job_id, user_id, jd_text, session_factory, company=company, role=role)
                pipeline_total.labels(status="completed").inc()
            except Exception as e:
                import traceback
                logger.error(f"Pipeline FAILED for job {job_id}: {e}\n{traceback.format_exc()}")
                async with session_factory() as db:
                    await db.execute(
                        update(Application)
                        .where(Application.id == job_id)
                        .values(pipeline_status="failed")
                    )
                    await db.commit()
                await manager.send_progress(job_id, {
                    "agent": "pipeline",
                    "status": "failed",
                    "message": str(e),
                })
                pipeline_total.labels(status="failed").inc()
            finally:
                pipeline_duration_seconds.observe(time.monotonic() - start)
                active_pipelines.dec()
                try:
                    await flush_langfuse()
                except Exception:
                    pass
        finally:
            await engine.dispose()

    asyncio.run(_run())


@celery_app.task(name="app.celery_app.tasks.check_stale_applications")
def check_stale_applications():
    cutoff = datetime.utcnow() - timedelta(days=7)

    async def _run():
        engine = _make_engine()
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        try:
            async with session_factory() as db:
                result = await db.execute(
                    select(Application).where(
                        Application.status.in_(["applied", "interview"]),
                        Application.updated_at < cutoff,
                        Application.pipeline_status == "completed",
                    )
                )
                stale = result.scalars().all()
                for app in stale:
                    await manager.send_progress(app.user_id, {
                        "type": "reminder",
                        "message": f"No update on your {app.role} application at {app.company} in 7 days",
                    })
        finally:
            await engine.dispose()

    asyncio.run(_run())


@celery_app.task(name="app.celery_app.tasks.cleanup_old_jobs")
def cleanup_old_jobs():
    cutoff = datetime.utcnow() - timedelta(days=90)

    async def _run():
        engine = _make_engine()
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        try:
            async with session_factory() as db:
                result = await db.execute(
                    delete(Application)
                    .where(
                        Application.status == "rejected",
                        Application.created_at < cutoff,
                    )
                    .returning(Application.id)
                )
                count = len(result.fetchall())
                await db.commit()
                logger.info(f"cleanup_old_jobs: deleted {count} rejected applications older than 90 days")
        finally:
            await engine.dispose()

    asyncio.run(_run())
