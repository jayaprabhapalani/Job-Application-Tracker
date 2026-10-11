import asyncio
from datetime import datetime, timedelta
from app.monitoring.logger import logger
from sqlalchemy import select, update, delete
import time
from app.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.agents.orchestrator import run_pipeline
from app.jobs.models import Application
from app.websocket.manager import manager
from app.monitoring.metrics import pipeline_total, pipeline_duration_seconds, active_pipelines


@celery_app.task(name="app.celery_app.tasks.run_agent_pipeline")
def run_agent_pipeline(job_data: dict):
    job_id = job_data["job_id"]
    user_id = job_data.get("user_id", "")
    jd_text = job_data.get("jd_text", "")

    async def _run():
        async with AsyncSessionLocal() as db:
            await db.execute(
                update(Application)
                .where(Application.id == job_id)
                .values(pipeline_status="running")
            )
            await db.commit()
            active_pipelines.inc()
            start = time.monotonic()
            try:
                await run_pipeline(job_id, user_id, jd_text, db)
                pipeline_total.labels(status="completed").inc()
            except Exception as e:
                import traceback
                logger.error(f"Pipeline FAILED for job {job_id}: {e}\n{traceback.format_exc()}")
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

    asyncio.get_event_loop().run_until_complete(_run())


@celery_app.task(name="app.celery_app.tasks.check_stale_applications")
def check_stale_applications():
    cutoff = datetime.utcnow() - timedelta(days=7)

    async def _run():
        async with AsyncSessionLocal() as db:
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

    asyncio.get_event_loop().run_until_complete(_run())


@celery_app.task(name="app.celery_app.tasks.cleanup_old_jobs")
def cleanup_old_jobs():
    cutoff = datetime.utcnow() - timedelta(days=90)

    async def _run():
        async with AsyncSessionLocal() as db:
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

    asyncio.get_event_loop().run_until_complete(_run())
