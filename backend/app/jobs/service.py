from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException

from app.jobs.models import Application, Resume


async def create_application(db: AsyncSession, user_id: str, data) -> Application:
    app = Application(
        user_id=user_id,
        company=data.company,
        role=data.role,
        jd_text=data.jd_text,
        jd_url=data.jd_url,
    )
    db.add(app)
    await db.commit()
    await db.refresh(app)
    return app


async def get_applications(db: AsyncSession, user_id: str) -> list[Application]:
    result = await db.execute(
        select(Application)
        .where(Application.user_id == user_id)
        .order_by(Application.created_at.desc())
    )
    return result.scalars().all()


async def get_application(db: AsyncSession, user_id: str, app_id: str) -> Application:
    result = await db.execute(
        select(Application).where(Application.id == app_id, Application.user_id == user_id)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


async def update_application_status(db: AsyncSession, app_id: str, status: str) -> None:
    await db.execute(
        update(Application).where(Application.id == app_id).values(status=status)
    )
    await db.commit()


async def update_pipeline_status(db: AsyncSession, app_id: str, status: str) -> None:
    await db.execute(
        update(Application).where(Application.id == app_id).values(pipeline_status=status)
    )
    await db.commit()


async def create_resume(db: AsyncSession, user_id: str, content: str) -> Resume:
    await db.execute(
        update(Resume).where(Resume.user_id == user_id).values(is_active=False)
    )
    resume = Resume(user_id=user_id, content=content)
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    return resume


async def get_active_resume(db: AsyncSession, user_id: str) -> Resume | None:
    result = await db.execute(
        select(Resume).where(Resume.user_id == user_id, Resume.is_active == True)
    )
    return result.scalar_one_or_none()
