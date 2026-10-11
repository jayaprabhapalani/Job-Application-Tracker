from prometheus_client import Counter, Histogram, Gauge

pipeline_total = Counter(
    "pipeline_total",
    "Total pipeline runs by status",
    ["status"],
)

pipeline_duration_seconds = Histogram(
    "pipeline_duration_seconds",
    "Full pipeline run duration in seconds",
)

active_pipelines = Gauge(
    "active_pipelines",
    "Number of currently running pipelines",
)

agent_duration_seconds = Histogram(
    "agent_duration_seconds",
    "Per-agent run duration in seconds",
    ["agent_name"],
)
