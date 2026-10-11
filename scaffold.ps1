$ErrorActionPreference = 'Stop'

$directories = @(
    'backend/app/auth',
    'backend/app/jobs',
    'backend/app/agents',
    'backend/app/agents/guardrails',
    'backend/app/rag',
    'backend/app/kafka',
    'backend/app/celery_app',
    'backend/app/websocket',
    'backend/app/monitoring',
    'backend/app/middleware',
    'backend/alembic',
    'backend/tests',
    'frontend/src/pages',
    'frontend/src/components',
    'frontend/src/hooks',
    '.github/workflows'
)

$files = @(
    'backend/app/main.py',
    'backend/app/config.py',
    'backend/app/database.py',
    'backend/app/redis_client.py',
    'backend/app/auth/router.py',
    'backend/app/auth/models.py',
    'backend/app/auth/schemas.py',
    'backend/app/auth/utils.py',
    'backend/app/jobs/router.py',
    'backend/app/jobs/models.py',
    'backend/app/jobs/schemas.py',
    'backend/app/jobs/service.py',
    'backend/app/agents/orchestrator.py',
    'backend/app/agents/jd_parser.py',
    'backend/app/agents/resume_tailor.py',
    'backend/app/agents/cover_letter.py',
    'backend/app/agents/company_research.py',
    'backend/app/agents/interview_prep.py',
    'backend/app/agents/guardrails/input_validator.py',
    'backend/app/agents/guardrails/output_validator.py',
    'backend/app/agents/guardrails/schemas.py',
    'backend/app/rag/embeddings.py',
    'backend/app/rag/vector_store.py',
    'backend/app/rag/retriever.py',
    'backend/app/kafka/producer.py',
    'backend/app/kafka/consumer.py',
    'backend/app/kafka/topics.py',
    'backend/app/celery_app/worker.py',
    'backend/app/celery_app/tasks.py',
    'backend/app/celery_app/beat_schedule.py',
    'backend/app/websocket/manager.py',
    'backend/app/monitoring/metrics.py',
    'backend/app/monitoring/logger.py',
    'backend/app/middleware/rate_limiter.py',
    'backend/app/middleware/auth_middleware.py',
    'backend/tests/.gitkeep',
    'backend/Dockerfile',
    'backend/requirements.txt',
    'backend/.env',
    'frontend/src/pages/Dashboard.jsx',
    'frontend/src/pages/NewApplication.jsx',
    'frontend/src/pages/ApplicationDetail.jsx',
    'frontend/src/hooks/useWebSocket.js',
    'frontend/package.json',
    'docker-compose.yml',
    '.github/workflows/ci.yml',
    'README.md'
)

foreach ($directory in $directories) {
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
}

foreach ($file in $files) {
    if (-not (Test-Path -LiteralPath $file)) {
        New-Item -ItemType File -Path $file | Out-Null
    }
}

Write-Output "Scaffold created under $((Get-Location).Path)"
