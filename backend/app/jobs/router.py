from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.jobs import schemas, service
from app.kafka.producer import publish_event
from app.kafka.topics import ANALYSIS_REQUESTS
from app.rag.vector_store import chunk_text, store_chunks, delete_chunks

router = APIRouter()


def _extract_text_from_file(filename: str, data: bytes) -> str:
    ext = filename.rsplit('.', 1)[-1].lower()
    if ext == 'pdf':
        import fitz
        doc = fitz.open(stream=data, filetype='pdf')
        return '\n'.join(page.get_text() for page in doc)
    elif ext in ('docx', 'doc'):
        import docx, io
        doc = docx.Document(io.BytesIO(data))
        return '\n'.join(p.text for p in doc.paragraphs if p.text.strip())
    elif ext == 'txt':
        return data.decode('utf-8', errors='ignore')
    else:
        raise HTTPException(status_code=400, detail=f'Unsupported file type: .{ext}. Use PDF, DOCX, or TXT.')


@router.post('/resume', response_model=schemas.ResumeResponse)
async def upload_resume(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    file: Optional[UploadFile] = File(None),
    content: Optional[str] = Form(None),
):
    if file and file.filename:
        raw = await file.read()
        text = _extract_text_from_file(file.filename, raw)
    elif content:
        text = content
    else:
        raise HTTPException(status_code=400, detail='Provide either a file or content.')

    await delete_chunks(db, current_user.id, source='resume')
    chunks = chunk_text(text)
    await store_chunks(db, current_user.id, chunks, source='resume')
    resume = await service.create_resume(db, current_user.id, text)
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
        {"job_id": str(app.id), "user_id": current_user.id, "jd_text": payload.jd_text,
         "company": payload.company, "role": payload.role},
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
