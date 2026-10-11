from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.jobs import schemas, service
from app.kafka.producer import publish_event
from app.kafka.topics import ANALYSIS_REQUESTS
from app.rag.vector_store import chunk_text, store_chunks, delete_chunks

router = APIRouter()


@router.post("/resume", response_model=schemas.ResumeResponse)
async def upload_resume(
    payload: schemas.ResumeCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    await delete_chunks(db, current_user.id, source="resume")
    chunks = chunk_text(payload.content)
    await store_chunks(db, current_user.id, chunks, source="resume")
    resume = await service.create_resume(db, current_user.id, payload.content)
    return resume


@router.get("/resume", response_model=schemas.ResumeResponse | None)
async def get_active_resume(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    resume = await service.get_active_resume(db, current_user.id)
    if not resume:
        raise HTTPException(status_code=404, detail="No active resume found")
    return resume


@router.post("/", response_model=schemas.ApplicationResponse)
async def create_job(
    payload: schemas.ApplicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    app = await service.create_application(db, current_user.id, payload)

    await publish_event(
        ANALYSIS_REQUESTS,
        str(app.id),
        {"job_id": str(app.id), "user_id": current_user.id, "jd_text": payload.jd_text},
    )

    return app


@router.get("/", response_model=list[schemas.ApplicationResponse])
async def list_jobs(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    return await service.get_applications(db, current_user.id)


@router.get("/{app_id}", response_model=schemas.ApplicationResponse)
async def get_job(
    app_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    return await service.get_application(db, current_user.id, app_id)


@router.patch("/{app_id}/status")
async def update_job_status(
    app_id: str,
    payload: schemas.ApplicationStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    await service.update_application_status(db, app_id, payload.status)
    return {"status": "ok"}
