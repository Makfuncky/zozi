#!/usr/bin/env python3
"""
ZOZI Audit — Section Checkers for Laws 251-325.
Each function checks a category of architecture laws using the global helpers
(f, read, rel, read_lines, parse_ast, etc.) defined in full_system_audit.py.

Called by main() after index_files() has populated the global file lists.
"""

import re
import ast
from pathlib import Path


# ══════════════════════════════════════════════════════════════
# SECTION 7: SCALABILITY (Laws 251-270)
# ══════════════════════════════════════════════════════════════

def check_section_scalability():
    """Laws 251-270: Scalability — horizontal scaling, auto-scaling, partitioning, CQRS, caching."""
    _law_251_horizontal_scaling()
    _law_252_auto_scaling()
    _law_253_partitioning()
    _law_254_cqrs()
    _law_255_write_behind_cache()
    _law_256_tenant_quotas()
    _law_257_fulltext_search()
    _law_258_image_pipeline()
    _law_259_api_caching()
    _law_260_pgbouncer()
    _law_261_read_replicas()
    _law_262_archiving()
    _law_263_write_buffering()
    _law_264_static_assets()
    _law_265_db_monitoring()
    _law_266_synthetic_monitoring()
    _law_267_endpoint_limits()
    _law_268_load_shedding()
    _law_269_cost_optimization()
    _law_270_chaos_engineering()


def _law_251_horizontal_scaling():
    """Law 251: N stateless replicas. Sessions in Redis."""
    # Check for session storage configuration
    session_files = [p for p in ALL_PY if 'session' in p.name.lower() or 'session' in read(p).lower()]
    has_redis_sessions = False

    for p in session_files:
        content = read(p)
        if re.search(r'redis|Redis|REDIS', content) and re.search(r'session|Session|SESSION', content):
            has_redis_sessions = True
            break

    # Check middleware for session handling
    for p in MIDDLEWARE_FILES:
        content = read(p)
        if re.search(r'session|Session', content) and re.search(r'redis|Redis', content):
            has_redis_sessions = True
            break

    # Check config files
    config_paths = [
        ROOT / "core" / "config.py",
        ROOT / "config.py",
        ROOT / "settings.py",
        ROOT / ".env.example",
    ]
    for cp in config_paths:
        if cp.exists():
            content = read(cp)
            if re.search(r'SESSION.*REDIS|REDIS.*SESSION|SESSION_BACKEND.*redis', content, re.IGNORECASE):
                has_redis_sessions = True
                break

    if not has_redis_sessions:
        f(251, "Scalability", "high", "backend", 0,
          "No Redis-based session storage detected — horizontal scaling requires stateless "
          "replicas with shared session storage in Redis (Law 251).",
          "Configure Redis-backed sessions:\n"
          "  SESSION_BACKEND='redis'\n"
          "  REDIS_SESSION_URL=redis://localhost:6379/1\n"
          "Use fastapi-session or starlette SessionMiddleware with Redis backend.")


def _law_252_auto_scaling():
    """Law 252: CPU > 70% scale up. Min 2, max 20."""
    # Check for auto-scaling configuration in deployment files
    deploy_paths = [
        ROOT.parent / "docker-compose.yml",
        ROOT.parent / "docker-compose.prod.yml",
        ROOT.parent / "k8s" / "deployment.yml",
        ROOT.parent / "k8s" / "hpa.yml",
    ]

    has_autoscaling = False
    for dp in deploy_paths:
        if dp.exists():
            content = read(dp)
            if re.search(r'hpa|autoscal|scale.*cpu|cpu.*scale|HorizontalPodAutoscaler', content, re.IGNORECASE):
                has_autoscaling = True
                break

    if not has_autoscaling:
        f(252, "Scalability", "medium", "backend", 0,
          "No auto-scaling configuration detected — system must scale based on CPU > 70% "
          "with min 2, max 20 replicas (Law 252).",
          "Add Kubernetes HPA or equivalent:\n"
          "  apiVersion: autoscaling/v2\n"
          "  kind: HorizontalPodAutoscaler\n"
          "  spec:\n"
          "    minReplicas: 2\n"
          "    maxReplicas: 20\n"
          "    metrics:\n"
          "    - type: Resource\n"
          "      resource:\n"
          "        name: cpu\n"
          "        target:\n"
          "          type: Utilization\n"
          "          averageUtilization: 70")


def _law_253_partitioning():
    """Law 253: Range partition by created_at."""
    # Check for partitioning patterns in models or migration files
    has_partitioning = False
    for p in MODELS:
        content = read(p)
        if re.search(r'partition|Partition|PARTITION', content):
            has_partitioning = True
            break

    # Check alembic migrations
    alembic_dir = ROOT / "alembic" / "versions"
    if alembic_dir.exists():
        for p in alembic_dir.glob("*.py"):
            content = read(p)
            if re.search(r'partition|Partition|PARTITION', content):
                has_partitioning = True
                break

    if not has_partitioning:
        f(253, "Scalability", "medium", "backend", 0,
          "No table partitioning detected — large tables must use range partitioning "
          "by created_at for query performance (Law 253).",
          "Implement PostgreSQL range partitioning:\n"
          "  CREATE TABLE orders (\n"
          "    id UUID, created_at TIMESTAMP, ...\n"
          "  ) PARTITION BY RANGE (created_at);\n"
          "  CREATE TABLE orders_2024 PARTITION OF orders\n"
          "    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');")


def _law_254_cqrs():
    """Law 254: Commands write. Events update read models."""
    # Check for CQRS patterns: command handlers, event handlers, read models
    has_commands = False
    has_events = False
    has_read_models = False

    for p in SERVICES:
        content = read(p)
        name = p.name.lower()
        if 'command' in name or 'handler' in name:
            has_commands = True
        if 'event' in name or 'subscriber' in name:
            has_events = True
        if 'read' in name or 'query' in name:
            has_read_models = True

    # Check for event-driven patterns
    for p in ALL_PY:
        content = read(p)
        if re.search(r'class\s+\w+Command|CommandHandler|CommandHandler', content):
            has_commands = True
        if re.search(r'class\s+\w+Event|EventHandler|EventSubscriber', content):
            has_events = True

    if not (has_commands and has_events):
        f(254, "Scalability", "medium", "backend", 0,
          "CQRS pattern not fully implemented — commands must write, events must update "
          "read models for scalable read/write separation (Law 254).",
          "Implement CQRS:\n"
          "  1. Create command handlers in domains/{d}/commands/\n"
          "  2. Create event handlers in domains/{d}/events/\n"
          "  3. Create read models in domains/{d}/read_models/\n"
          "  4. Commands emit events → events update read models")


def _law_255_write_behind_cache():
    """Law 255: Buffer in Redis, flush async."""
    # Check for write-behind caching patterns
    has_write_behind = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'write.behind|write_behind|buffer.*flush|flush.*buffer', content, re.IGNORECASE):
            has_write_behind = True
            break
        if re.search(r'redis.*queue|queue.*redis', content, re.IGNORECASE) and \
           re.search(r'flush|persist|save', content, re.IGNORECASE):
            has_write_behind = True
            break

    if not has_write_behind:
        f(255, "Scalability", "low", "backend", 0,
          "No write-behind cache pattern detected — buffer writes in Redis and flush "
          "async for high-throughput scenarios (Law 255).",
          "Implement write-behind caching:\n"
          "  1. Write to Redis list/queue immediately\n"
          "  2. Background worker flushes to DB in batches\n"
          "  3. Use Celery beat or APScheduler for periodic flush")


def _law_256_tenant_quotas():
    """Law 256: Per-country limits. 429 on exceed."""
    # Check for quota enforcement
    has_quotas = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'quota|limit.*country|country.*limit', content, re.IGNORECASE):
            has_quotas = True
            break
        if re.search(r'429|Too Many Requests|rate.limit', content):
            has_quotas = True
            break

    # Check middleware for rate limiting
    for p in MIDDLEWARE_FILES:
        content = read(p)
        if re.search(r'quota|rate.*limit|limit.*request', content, re.IGNORECASE):
            has_quotas = True
            break

    if not has_quotas:
        f(256, "Scalability", "high", "backend", 0,
          "No tenant quota enforcement detected — per-country limits with 429 response "
          "on exceed are required for multi-tenant scalability (Law 256).",
          "Implement tenant quotas:\n"
          "  1. Add quota middleware checking per-country limits\n"
          "  2. Store quotas in Redis with TTL\n"
          "  3. Return HTTP 429 when quota exceeded\n"
          "  4. Add Retry-After header")


def _law_257_fulltext_search():
    """Law 257: Elasticsearch/OpenSearch for catalog."""
    # Check for search engine usage
    has_search = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'elasticsearch|opensearch|Elasticsearch|OpenSearch', content):
            has_search = True
            break

    # Check providers for search
    for p in PROVIDERS:
        content = read(p)
        if re.search(r'search|elastic|opensearch', content, re.IGNORECASE):
            has_search = True
            break

    if not has_search:
        f(257, "Scalability", "medium", "backend", 0,
          "No full-text search engine detected — catalog search must use "
          "Elasticsearch or OpenSearch (Law 257).",
          "Add search provider:\n"
          "  1. Create providers/search/ with Elasticsearch client\n"
          "  2. Index catalog products on create/update\n"
          "  3. Route search queries to ES/OpenSearch\n"
          "  4. Implement fallback to DB ILIKE for degraded mode")


def _law_258_image_pipeline():
    """Law 258: Async resize, WebP, metadata strip."""
    # Check for image processing
    has_image_pipeline = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'webp|WebP|resize|thumbnail|pillow|PIL', content, re.IGNORECASE):
            has_image_pipeline = True
            break
        if re.search(r'exif|metadata.*strip|strip.*metadata', content, re.IGNORECASE):
            has_image_pipeline = True
            break

    if not has_image_pipeline:
        f(258, "Scalability", "medium", "backend", 0,
          "No image pipeline detected — images must be resized async, converted to WebP, "
          "and have metadata stripped (Law 258).",
          "Implement image pipeline:\n"
          "  1. Use Pillow or Pillow-SIMD for resize\n"
          "  2. Convert to WebP format\n"
          "  3. Strip EXIF metadata\n"
          "  4. Process via Celery task asynchronously")


def _law_259_api_caching():
    """Law 259: ETag, Last-Modified, Cache-Control."""
    # Check for caching headers
    has_caching = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'ETag|Last-Modified|Cache-Control|cache_control', content):
            has_caching = True
            break

    # Check middleware
    for p in MIDDLEWARE_FILES:
        content = read(p)
        if re.search(r'cache|etag|Cache-Control', content, re.IGNORECASE):
            has_caching = True
            break

    if not has_caching:
        f(259, "Scalability", "medium", "backend", 0,
          "No API caching headers detected — responses must include ETag, Last-Modified, "
          "and Cache-Control headers (Law 259).",
          "Add caching middleware:\n"
          "  response.headers['Cache-Control'] = 'public, max-age=300'\n"
          "  response.headers['ETag'] = generate_etag(content)\n"
          "  Support If-None-Match for 304 responses")


def _law_260_pgbouncer():
    """Law 260: PgBouncer transaction pooling."""
    # Check for PgBouncer configuration
    has_pgbouncer = False
    config_paths = [
        ROOT.parent / "docker-compose.yml",
        ROOT.parent / "docker-compose.prod.yml",
    ]
    for cp in config_paths:
        if cp.exists():
            content = read(cp)
            if re.search(r'pgbouncer|PgBouncer|pg-bouncer', content, re.IGNORECASE):
                has_pgbouncer = True
                break

    # Check database config
    for p in INFRA:
        content = read(p)
        if re.search(r'pgbouncer|pool_size|Pool', content):
            has_pgbouncer = True
            break

    if not has_pgbouncer:
        f(260, "Scalability", "medium", "backend", 0,
          "No PgBouncer configuration detected — transaction pooling required for "
          "database connection scalability (Law 260).",
          "Add PgBouncer:\n"
          "  1. Deploy PgBouncer between app and PostgreSQL\n"
          "  2. Set pool_mode = transaction\n"
          "  3. Configure max_client_conn = 10000\n"
          "  4. Set default_pool_size = 25")


def _law_261_read_replicas():
    """Law 261: Auto-route reads."""
    # Check for read replica configuration
    has_read_replicas = False
    for p in INFRA:
        content = read(p)
        if re.search(r'read.*replica|replica.*read|READ_REPLICA|read_replica', content, re.IGNORECASE):
            has_read_replicas = True
            break
        if re.search(r'session.*bind|bind.*engine|routing.*session', content, re.IGNORECASE):
            has_read_replicas = True
            break

    if not has_read_replicas:
        f(261, "Scalability", "medium", "backend", 0,
          "No read replica routing detected — reads must be auto-routed to replicas "
          "for read scalability (Law 261).",
          "Implement read replica routing:\n"
          "  1. Configure multiple SQLAlchemy engines (primary + replicas)\n"
          "  2. Use session.bind_mapper() or custom Session routing\n"
          "  3. Route SELECT queries to replicas\n"
          "  4. Route writes to primary")


def _law_262_archiving():
    """Law 262: Old data to S3 Glacier."""
    # Check for archiving patterns
    has_archiving = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'glacier|archiv.*s3|s3.*archiv|cold.*storage', content, re.IGNORECASE):
            has_archiving = True
            break
        if re.search(r'archive.*old|old.*data|retention.*policy', content, re.IGNORECASE):
            has_archiving = True
            break

    if not has_archiving:
        f(262, "Scalability", "low", "backend", 0,
          "No data archiving pattern detected — old data must be moved to S3 Glacier "
          "for cost-effective long-term storage (Law 262).",
          "Implement data archiving:\n"
          "  1. Create archive service in infrastructure/\n"
          "  2. Move records older than retention period to S3/Glacier\n"
          "  3. Use S3 lifecycle policies for Glacier transition\n"
          "  4. Keep archive metadata in DB for retrieval")


def _law_263_write_buffering():
    """Law 263: Celery queue for bursty writes."""
    # Check for Celery task usage
    has_celery = False
    for p in JOBS:
        content = read(p)
        if re.search(r'celery|@task|@shared_task', content, re.IGNORECASE):
            has_celery = True
            break

    for p in ALL_PY:
        content = read(p)
        if re.search(r'celery|@app\.task|@shared_task', content, re.IGNORECASE):
            has_celery = True
            break

    if not has_celery:
        f(263, "Scalability", "medium", "backend", 0,
          "No write buffering queue detected — bursty writes must be buffered in "
          "Celery queue for smooth processing (Law 263).",
          "Implement write buffering:\n"
          "  1. Configure Celery with Redis/RabbitMQ broker\n"
          "  2. Route bursty writes through Celery tasks\n"
          "  3. Use task rate limiting for DB protection\n"
          "  4. Implement idempotent tasks for retry safety")


def _law_264_static_assets():
    """Law 264: Minify, compress, hash, CDN."""
    # Check for static asset configuration
    has_static_config = False
    frontend_paths = [
        ROOT.parent / "frontend" / "web_app" / "next.config.js",
        ROOT.parent / "frontend" / "web_app" / "next.config.mjs",
    ]
    for fp in frontend_paths:
        if fp.exists():
            content = read(fp)
            if re.search(r'cdn|assetPrefix|static.*optim', content, re.IGNORECASE):
                has_static_config = True
                break

    if not has_static_config:
        f(264, "Scalability", "low", "frontend", 0,
          "No static asset optimization detected — assets must be minified, compressed, "
          "hashed, and served via CDN (Law 264).",
          "Configure static assets:\n"
          "  1. Enable Next.js built-in minification\n"
          "  2. Configure assetPrefix for CDN\n"
          "  3. Enable gzip/brotli compression\n"
          "  4. Use content-hashed filenames")


def _law_265_db_monitoring():
    """Law 265: Alerts on connections, lag, deadlocks."""
    # Check for DB monitoring
    has_db_monitoring = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'deadlock|connection.*pool|pool.*overflow|db.*lag|replication.*lag', content, re.IGNORECASE):
            has_db_monitoring = True
            break

    if not has_db_monitoring:
        f(265, "Scalability", "medium", "backend", 0,
          "No database monitoring detected — alerts required for connection pool, "
          "replication lag, and deadlocks (Law 265).",
          "Add DB monitoring:\n"
          "  1. Monitor pool_size, overflow, checkedout connections\n"
          "  2. Alert on replication lag > 10s\n"
          "  3. Alert on deadlock detection\n"
          "  4. Use pg_stat_statements for slow query alerts")


def _law_266_synthetic_monitoring():
    """Law 266: Every 60s from multiple regions."""
    # Check for synthetic monitoring configuration
    has_synthetic = False
    monitor_paths = [
        ROOT.parent / "monitoring" / "synthetic.py",
        ROOT.parent / "scripts" / "synthetic_check.py",
    ]
    for mp in monitor_paths:
        if mp.exists():
            has_synthetic = True
            break

    if not has_synthetic:
        f(266, "Scalability", "low", "backend", 0,
          "No synthetic monitoring detected — health checks every 60s from multiple "
          "regions required for availability monitoring (Law 266).",
          "Implement synthetic monitoring:\n"
          "  1. Use Pingdom, Datadog Synthetics, or Grafana Cloud\n"
          "  2. Check critical endpoints every 60s\n"
          "  3. Deploy probes from ≥3 geographic regions\n"
          "  4. Alert on 2+ region failures")


def _law_267_endpoint_limits():
    """Law 267: Max body (10MB), query (100 items), time (30s)."""
    # Check for endpoint limits
    has_body_limit = False
    has_pagination_limit = False
    has_timeout = False

    for p in MIDDLEWARE_FILES:
        content = read(p)
        if re.search(r'max.*body|body.*limit|content.*length|MAX_BODY', content, re.IGNORECASE):
            has_body_limit = True
        if re.search(r'timeout|TIMEOUT|request.*time', content, re.IGNORECASE):
            has_timeout = True

    for p in ROUTERS:
        content = read(p)
        if re.search(r'page_size|per_page|max.*items|limit.*default', content, re.IGNORECASE):
            has_pagination_limit = True

    if not has_body_limit:
        f(267, "Scalability", "high", "backend", 0,
          "No request body size limit detected — max body must be 10MB to prevent "
          "memory exhaustion (Law 267).",
          "Add body size limit middleware:\n"
          "  app.add_middleware(MaxBodySizeMiddleware, max_size=10*1024*1024)\n"
          "  Return HTTP 413 when limit exceeded")

    if not has_pagination_limit:
        f(267, "Scalability", "medium", "backend", 0,
          "No pagination limit detected — query results must be capped at 100 items "
          "per page (Law 267).",
          "Add pagination limits:\n"
          "  page_size: int = Query(default=20, le=100)\n"
          "  Return 400 for page_size > 100")

    if not has_timeout:
        f(267, "Scalability", "medium", "backend", 0,
          "No request timeout detected — endpoints must timeout at 30s (Law 267).",
          "Add request timeout:\n"
          "  app.add_middleware(TimeoutMiddleware, timeout=30)\n"
          "  Return HTTP 504 on timeout")


def _law_268_load_shedding():
    """Law 268: Shed non-critical first."""
    # Check for load shedding patterns
    has_load_shedding = False
    for p in MIDDLEWARE_FILES:
        content = read(p)
        if re.search(r'load.*shed|shedd|priority.*queue|circuit.*break', content, re.IGNORECASE):
            has_load_shedding = True
            break

    if not has_load_shedding:
        f(268, "Scalability", "medium", "backend", 0,
          "No load shedding mechanism detected — non-critical requests must be shed "
          "first under high load (Law 268).",
          "Implement load shedding:\n"
          "  1. Add priority header to requests (critical/normal/low)\n"
          "  2. Shed low-priority when CPU > 80%\n"
          "  3. Return 503 with Retry-After for shed requests\n"
          "  4. Protect critical paths (checkout, payment)")


def _law_269_cost_optimization():
    """Law 269: Right-size, spot instances."""
    # Check for cost optimization configuration
    has_cost_opt = False
    deploy_paths = [
        ROOT.parent / "docker-compose.prod.yml",
        ROOT.parent / "k8s",
    ]
    for dp in deploy_paths:
        if dp.exists():
            if dp.is_dir():
                for p in safe_rglob(dp):
                    if p.is_file():
                        content = read(p)
                        if re.search(r'spot|preemptible|right.*size|resource.*request', content, re.IGNORECASE):
                            has_cost_opt = True
                            break
            else:
                content = read(dp)
                if re.search(r'spot|preemptible|right.*size', content, re.IGNORECASE):
                    has_cost_opt = True
                    break

    if not has_cost_opt:
        f(269, "Scalability", "low", "backend", 0,
          "No cost optimization configuration detected — use spot instances and "
          "right-size resources for cost efficiency (Law 269).",
          "Implement cost optimization:\n"
          "  1. Use spot/preemptible instances for workers\n"
          "  2. Right-size resource requests vs usage\n"
          "  3. Set up cluster autoscaler\n"
          "  4. Use reserved instances for baseline load")


def _law_270_chaos_engineering():
    """Law 270: Regular failure experiments."""
    # Check for chaos engineering configuration
    has_chaos = False
    chaos_paths = [
        ROOT.parent / "chaos",
        ROOT.parent / "scripts" / "chaos",
        ROOT.parent / "tests" / "chaos",
    ]
    for cp in chaos_paths:
        if cp.exists():
            has_chaos = True
            break

    if not has_chaos:
        f(270, "Scalability", "low", "backend", 0,
          "No chaos engineering detected — regular failure experiments required "
          "to validate resilience (Law 270).",
          "Implement chaos engineering:\n"
          "  1. Use Chaos Mesh or Litmus for k8s\n"
          "  2. Test: pod kill, network latency, DB failover\n"
          "  3. Run experiments in staging weekly\n"
          "  4. Document and track findings")


# ══════════════════════════════════════════════════════════════
# SECTION 8: SECURITY HARDENING (Laws 271-295)
# ══════════════════════════════════════════════════════════════

def check_section_security_hardening():
    """Laws 271-295: Security Hardening — AI security, encryption, headers, compliance."""
    _law_271_ai_agent_security()
    _law_272_data_exfiltration()
    _law_273_model_poisoning()
    _law_274_adversarial_detection()
    _law_275_encryption_at_rest()
    _law_276_encryption_in_transit()
    _law_277_key_rotation()
    _law_278_worm_audit()
    _law_279_session_binding()
    _law_280_brute_force_db()
    _law_281_bot_detection()
    _law_282_pii_masking()
    _law_283_mfa()
    _law_284_zero_trust()
    _law_285_csp()
    _law_286_sri()
    _law_287_security_headers()
    _law_288_disclosure_process()
    _law_289_pen_testing()
    _law_290_dep_pinning()
    _law_291_sbom()
    _law_292_license_compliance()
    _law_293_incident_automation()
    _law_294_security_training()
    _law_295_supply_chain()


def _law_271_ai_agent_security():
    """Law 271: Prompt injection prevention."""
    # Check for AI/LLM usage and prompt injection prevention
    has_ai = False
    has_prompt_safety = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'openai|anthropic|llm|prompt|chatgpt|gpt', content, re.IGNORECASE):
            has_ai = True
        if re.search(r'prompt.*inject|inject.*prevent|sanitize.*input|validate.*prompt', content, re.IGNORECASE):
            has_prompt_safety = True

    if has_ai and not has_prompt_safety:
        f(271, "Security", "critical", "backend", 0,
          "AI/LLM usage detected without prompt injection prevention — all LLM inputs "
          "must be sanitized and validated (Law 271).",
          "Add prompt injection prevention:\n"
          "  1. Sanitize user input before passing to LLM\n"
          "  2. Use system prompts with clear boundaries\n"
          "  3. Validate LLM output before processing\n"
          "  4. Implement rate limiting on LLM endpoints")


def _law_272_data_exfiltration():
    """Law 272: Per-user export limits."""
    # Check for export functionality and limits
    has_export = False
    has_export_limits = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'export|download.*data|data.*export', content, re.IGNORECASE):
            has_export = True
        if re.search(r'export.*limit|limit.*export|max.*export|daily.*export', content, re.IGNORECASE):
            has_export_limits = True

    if has_export and not has_export_limits:
        f(272, "Security", "high", "backend", 0,
          "Data export functionality detected without per-user limits — export must "
          "be rate-limited per user to prevent data exfiltration (Law 272).",
          "Add export limits:\n"
          "  1. Limit exports to N per user per day\n"
          "  2. Track export volume per user\n"
          "  3. Alert on unusual export patterns\n"
          "  4. Require approval for bulk exports")


def _law_273_model_poisoning():
    """Law 273: ML input validation."""
    # Check for ML model usage and input validation
    has_ml = False
    has_ml_validation = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'model.*predict|predict.*model|ml.*model|sklearn|tensorflow|torch', content, re.IGNORECASE):
            has_ml = True
        if re.search(r'validate.*input|input.*valid|schema.*valid|bound.*check', content, re.IGNORECASE):
            has_ml_validation = True

    if has_ml and not has_ml_validation:
        f(273, "Security", "medium", "backend", 0,
          "ML model usage detected without input validation — ML inputs must be "
          "validated to prevent model poisoning (Law 273).",
          "Add ML input validation:\n"
          "  1. Validate input ranges and types\n"
          "  2. Check for adversarial patterns\n"
          "  3. Log anomalous inputs\n"
          "  4. Use input bounds checking")


def _law_274_adversarial_detection():
    """Law 274: Signature + anomaly detection."""
    # Check for adversarial detection
    has_adversarial = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'adversarial|anomaly.*detect|signature.*detect|fraud.*detect', content, re.IGNORECASE):
            has_adversarial = True
            break

    if not has_adversarial:
        f(274, "Security", "medium", "backend", 0,
          "No adversarial detection detected — signature and anomaly detection "
          "required for attack prevention (Law 274).",
          "Implement adversarial detection:\n"
          "  1. Add signature-based detection for known attacks\n"
          "  2. Add anomaly detection for unusual patterns\n"
          "  3. Integrate with fraud detection service\n"
          "  4. Alert on detected adversarial activity")


def _law_275_encryption_at_rest():
    """Law 275: AES-256. KMS."""
    # Check for encryption at rest configuration
    has_encryption = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'encrypt|AES|aes_256|cipher|kms', content, re.IGNORECASE):
            has_encryption = True
            break

    if not has_encryption:
        f(275, "Security", "high", "backend", 0,
          "No encryption at rest detected — sensitive data must be encrypted with "
          "AES-256 and managed via KMS (Law 275).",
          "Implement encryption at rest:\n"
          "  1. Use AES-256 for sensitive field encryption\n"
          "  2. Integrate with AWS KMS or HashiCorp Vault\n"
          "  3. Encrypt PII, payment data at application level\n"
          "  4. Enable PostgreSQL TDE for database encryption")


def _law_276_encryption_in_transit():
    """Law 276: TLS 1.3."""
    # Check for TLS configuration
    has_tls = False
    config_paths = [
        ROOT.parent / "docker-compose.prod.yml",
        ROOT.parent / "nginx.conf",
    ]
    for cp in config_paths:
        if cp.exists():
            content = read(cp)
            if re.search(r'tls|ssl|TLS|SSL', content, re.IGNORECASE):
                has_tls = True
                break

    if not has_tls:
        f(276, "Security", "high", "backend", 0,
          "No TLS configuration detected — all communication must use TLS 1.3 "
          "for encryption in transit (Law 276).",
          "Configure TLS 1.3:\n"
          "  1. Set minimum TLS version to 1.3\n"
          "  2. Use strong cipher suites only\n"
          "  3. Enable HSTS header\n"
          "  4. Use cert-manager for automatic certificate rotation")


def _law_277_key_rotation():
    """Law 277: Every 90 days."""
    # Check for key rotation configuration
    has_key_rotation = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'key.*rotat|rotat.*key|rotate.*secret|secret.*rotat', content, re.IGNORECASE):
            has_key_rotation = True
            break

    if not has_key_rotation:
        f(277, "Security", "medium", "backend", 0,
          "No key rotation policy detected — cryptographic keys must be rotated "
          "every 90 days (Law 277).",
          "Implement key rotation:\n"
          "  1. Automate key rotation every 90 days\n"
          "  2. Support multiple active keys for grace period\n"
          "  3. Use AWS KMS automatic rotation\n"
          "  4. Alert 7 days before rotation due")


def _law_278_worm_audit():
    """Law 278: Write Once Read Many."""
    # Check for WORM audit storage
    has_worm = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'worm|write.*once|immutable.*log|append.*only', content, re.IGNORECASE):
            has_worm = True
            break

    if not has_worm:
        f(278, "Security", "medium", "backend", 0,
          "No WORM audit storage detected — audit logs must be immutable "
          "(Write Once Read Many) (Law 278).",
          "Implement WORM audit:\n"
          "  1. Use append-only audit log storage\n"
          "  2. Enable S3 Object Lock for audit bucket\n"
          "  3. Hash chain audit entries for integrity\n"
          "  4. Separate audit storage account")


def _law_279_session_binding():
    """Law 279: Device fingerprint."""
    # Check for session binding
    has_session_binding = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'device.*fingerprint|fingerprint.*device|session.*bind|bind.*session', content, re.IGNORECASE):
            has_session_binding = True
            break

    if not has_session_binding:
        f(279, "Security", "medium", "backend", 0,
          "No session binding detected — sessions must be bound to device "
          "fingerprint to prevent session hijacking (Law 279).",
          "Implement session binding:\n"
          "  1. Generate device fingerprint on login\n"
          "  2. Store fingerprint hash with session\n"
          "  3. Validate fingerprint on each request\n"
          "  4. Require re-auth on fingerprint change")


def _law_280_brute_force_db():
    """Law 280: 5 fails = lock."""
    # Check for brute force protection
    has_brute_force = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'brute.*force|failed.*login|login.*attempt|account.*lock', content, re.IGNORECASE):
            has_brute_force = True
            break

    if not has_brute_force:
        f(280, "Security", "high", "backend", 0,
          "No brute force protection detected — 5 failed login attempts must "
          "trigger account lockout (Law 280).",
          "Implement brute force protection:\n"
          "  1. Track failed login attempts per account\n"
          "  2. Lock account after 5 failures\n"
          "  3. Use exponential backoff for lockout duration\n"
          "  4. Alert on brute force patterns")


def _law_281_bot_detection():
    """Law 281: Score + block/CAPTCHA."""
    # Check for bot detection
    has_bot_detection = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'bot.*detect|detect.*bot|captcha|recaptcha|hcaptcha|score.*request', content, re.IGNORECASE):
            has_bot_detection = True
            break

    if not has_bot_detection:
        f(281, "Security", "medium", "backend", 0,
          "No bot detection detected — request scoring with block/CAPTCHA "
          "required for bot prevention (Law 281).",
          "Implement bot detection:\n"
          "  1. Add request scoring middleware\n"
          "  2. Integrate reCAPTCHA v3 or hCaptcha\n"
          "  3. Block/Challenge high-score requests\n"
          "  4. Track and analyze bot patterns")


def _law_282_pii_masking():
    """Law 282: In logs, errors, non-admin responses."""
    # Check for PII masking
    has_pii_masking = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'mask.*pii|pii.*mask|mask.*email|mask.*phone|redact|sensitive.*data', content, re.IGNORECASE):
            has_pii_masking = True
            break

    if not has_pii_masking:
        f(282, "Security", "high", "backend", 0,
          "No PII masking detected — PII must be masked in logs, errors, "
          "and non-admin responses (Law 282).",
          "Implement PII masking:\n"
          "  1. Mask email: j***@example.com\n"
          "  2. Mask phone: +1******7890\n"
          "  3. Mask credit card: ****-****-****-1234\n"
          "  4. Apply in serializers and log formatters")


def _law_283_mfa():
    """Law 283: TOTP for admin/employee."""
    # Check for MFA enforcement
    has_mfa = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'mfa|totp|2fa|two.*factor|multi.*factor|authenticator', content, re.IGNORECASE):
            has_mfa = True
            break

    if not has_mfa:
        f(283, "Security", "high", "backend", 0,
          "No MFA enforcement detected — TOTP required for admin/employee "
          "accounts (Law 283).",
          "Implement MFA:\n"
          "  1. Add TOTP support using pyotp\n"
          "  2. Require MFA for admin/employee roles\n"
          "  3. Provide backup codes\n"
          "  4. Enforce on login for privileged roles")


def _law_284_zero_trust():
    """Law 284: mTLS service-to-service."""
    # Check for mTLS configuration
    has_mtls = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'mtls|mTLS|mutual.*tls|client.*cert|service.*mesh', content, re.IGNORECASE):
            has_mtls = True
            break

    if not has_mtls:
        f(284, "Security", "medium", "backend", 0,
          "No mTLS configuration detected — service-to-service communication "
          "must use mutual TLS (Law 284).",
          "Implement mTLS:\n"
          "  1. Deploy service mesh (Istio/Linkerd)\n"
          "  2. Issue service certificates\n"
          "  3. Require client certs for internal APIs\n"
          "  4. Use cert-manager for automation")


def _law_285_csp():
    """Law 285: Strict + nonces."""
    # Check for Content-Security-Policy headers
    has_csp = False
    for p in MIDDLEWARE_FILES:
        content = read(p)
        if re.search(r'content.security.policy|CSP|csp', content, re.IGNORECASE):
            has_csp = True
            break

    for p in ALL_PY:
        content = read(p)
        if re.search(r'Content-Security-Policy|content_security_policy', content):
            has_csp = True
            break

    if not has_csp:
        f(285, "Security", "high", "backend", 0,
          "No Content-Security-Policy header detected — strict CSP with nonces "
          "required to prevent XSS (Law 285).",
          "Add CSP header:\n"
          "  Content-Security-Policy:\n"
          "    default-src 'self';\n"
          "    script-src 'nonce-{random}';\n"
          "    style-src 'nonce-{random}';\n"
          "    img-src 'self' data:;")


def _law_286_sri():
    """Law 286: Integrity hashes."""
    # Check for Subresource Integrity
    has_sri = False
    frontend_root = ROOT.parent / "frontend" / "web_app"
    if frontend_root.exists():
        for p in safe_rglob(frontend_root):
            if p.is_file():
                content = read(p)
                if re.search(r'integrity.*sha|subresource.*integrity|sri', content, re.IGNORECASE):
                    has_sri = True
                    break

    if not has_sri:
        f(286, "Security", "low", "frontend", 0,
          "No Subresource Integrity detected — external scripts/styles must "
          "include integrity hashes (Law 286).",
          "Add SRI:\n"
          "  <script src='https://cdn.example.com/lib.js'\n"
          "          integrity='sha384-abc123'\n"
          "          crossorigin='anonymous'></script>")


def _law_287_security_headers():
    """Law 287: Permissions-Policy, COOP, CORP."""
    # Check for security headers
    has_security_headers = False
    required_headers = ['Permissions-Policy', 'Cross-Origin-Opener-Policy', 'Cross-Origin-Resource-Policy']
    for p in MIDDLEWARE_FILES:
        content = read(p)
        for header in required_headers:
            if header.lower() in content.lower():
                has_security_headers = True
                break

    if not has_security_headers:
        f(287, "Security", "medium", "backend", 0,
          "Missing security headers — Permissions-Policy, COOP, and CORP "
          "headers required (Law 287).",
          "Add security headers:\n"
          "  Permissions-Policy: camera=(), microphone=(), geolocation=()\n"
          "  Cross-Origin-Opener-Policy: same-origin\n"
          "  Cross-Origin-Resource-Policy: same-origin")


def _law_288_disclosure_process():
    """Law 288: SECURITY.md."""
    # Check for SECURITY.md
    security_md = ROOT.parent / "SECURITY.md"
    if not security_md.exists():
        f(288, "Security", "medium", "backend", 0,
          "No SECURITY.md found — vulnerability disclosure process "
          "must be documented (Law 288).",
          "Create SECURITY.md:\n"
          "  1. Document reporting process\n"
          "  2. List security contacts\n"
          "  3. Define response SLA\n"
          "  4. Include bounty program if applicable")


def _law_289_pen_testing():
    """Law 289: Annual third-party."""
    # Check for pen testing documentation
    has_pen_test = False
    docs_paths = [
        ROOT.parent / "docs" / "security",
        ROOT.parent / "docs",
    ]
    for dp in docs_paths:
        if dp.exists():
            for p in safe_rglob(dp):
                if p.is_file():
                    content = read(p)
                    if re.search(r'pen.*test|penetration.*test|security.*assessment', content, re.IGNORECASE):
                        has_pen_test = True
                        break

    if not has_pen_test:
        f(289, "Security", "low", "backend", 0,
          "No pen testing documentation found — annual third-party penetration "
          "testing required (Law 289).",
          "Document pen testing:\n"
          "  1. Schedule annual third-party pen test\n"
          "  2. Track findings and remediation\n"
          "  3. Store reports in docs/security/\n"
          "  4. Review scope annually")


def _law_290_dep_pinning():
    """Law 290: Exact + hashes."""
    # Check for dependency pinning
    req_files = list((ROOT.parent / "backend").glob("requirements*.txt"))
    has_pinned = False
    has_hashes = False
    for rf in req_files:
        content = read(rf)
        if '==' in content:
            has_pinned = True
        if '--hash=sha256' in content:
            has_hashes = True

    if not has_pinned:
        f(290, "Security", "medium", "backend", 0,
          "Dependencies not pinned to exact versions — all dependencies must "
          "use == version pinning (Law 290).",
          "Pin dependencies:\n"
          "  requirements.txt: package==1.2.3\n"
          "  Use pip-compile or poetry lock\n"
          "  Add --hash=sha256:abc... for each package")

    if has_pinned and not has_hashes:
        f(290, "Security", "medium", "backend", 0,
          "Dependencies pinned but without hashes — add SHA256 hashes for "
          "supply chain integrity (Law 290).",
          "Add hashes:\n"
          "  pip-compile --generate-hashes\n"
          "  Or: package==1.2.3 --hash=sha256:abc123...")


def _law_291_sbom():
    """Law 291: For every release."""
    # Check for SBOM generation
    has_sbom = False
    sbom_paths = [
        ROOT.parent / "scripts" / "generate_sbom.py",
        ROOT.parent / "Makefile",
    ]
    for sp in sbom_paths:
        if sp.exists():
            content = read(sp)
            if re.search(r'sbom|SBOM|software.*bill.*material', content, re.IGNORECASE):
                has_sbom = True
                break

    if not has_sbom:
        f(291, "Security", "low", "backend", 0,
          "No SBOM generation detected — Software Bill of Materials required "
          "for every release (Law 291).",
          "Implement SBOM:\n"
          "  1. Use cyclonedx-pip or syft\n"
          "  2. Generate SBOM in CI pipeline\n"
          "  3. Attach SBOM to release artifacts\n"
          "  4. Update SBOM on dependency changes")


def _law_292_license_compliance():
    """Law 292: CI-enforced."""
    # Check for license compliance checks
    has_license_check = False
    ci_paths = [
        ROOT.parent / ".github" / "workflows",
    ]
    for cp in ci_paths:
        if cp.exists():
            for p in safe_rglob(cp):
                if p.is_file():
                    content = read(p)
                    if re.search(r'license|licence|compliance|fossa|blackduck', content, re.IGNORECASE):
                        has_license_check = True
                        break

    if not has_license_check:
        f(292, "Security", "low", "backend", 0,
          "No license compliance check detected — license compliance must be "
          "enforced in CI pipeline (Law 292).",
          "Add license compliance:\n"
          "  1. Use pip-licenses or fossa\n"
          "  2. Block GPL/AGPL in CI\n"
          "  3. Generate license report\n"
          "  4. Define allowed licenses list")


def _law_293_incident_automation():
    """Law 293: Auto-isolate, revoke, capture."""
    # Check for incident automation
    has_incident_auto = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'auto.*isolat|isolat.*auto|revoke.*session|capture.*state', content, re.IGNORECASE):
            has_incident_auto = True
            break

    if not has_incident_auto:
        f(293, "Security", "medium", "backend", 0,
          "No incident automation detected — auto-isolate, revoke, and capture "
          "required for incident response (Law 293).",
          "Implement incident automation:\n"
          "  1. Auto-isolate compromised services\n"
          "  2. Revoke sessions on breach detection\n"
          "  3. Capture system state for forensics\n"
          "  4. Integrate with PagerDuty/Opsgenie")


def _law_294_security_training():
    """Law 294: Annual. OWASP + social engineering."""
    # Check for security training documentation
    has_training = False
    docs_paths = [
        ROOT.parent / "docs" / "security",
        ROOT.parent / "docs",
    ]
    for dp in docs_paths:
        if dp.exists():
            for p in safe_rglob(dp):
                if p.is_file():
                    content = read(p)
                    if re.search(r'training|owasp|social.*engineer|security.*aware', content, re.IGNORECASE):
                        has_training = True
                        break

    if not has_training:
        f(294, "Security", "low", "backend", 0,
          "No security training documentation found — annual security training "
          "(OWASP + social engineering) required (Law 294).",
          "Document security training:\n"
          "  1. Schedule annual training for all engineers\n"
          "  2. Cover OWASP Top 10\n"
          "  3. Include social engineering awareness\n"
          "  4. Track completion in HR system")


def _law_295_supply_chain():
    """Law 295: Image scanning + signing."""
    # Check for supply chain security
    has_supply_chain = False
    ci_paths = [
        ROOT.parent / ".github" / "workflows",
    ]
    for cp in ci_paths:
        if cp.exists():
            for p in safe_rglob(cp):
                if p.is_file():
                    content = read(p)
                    if re.search(r'trivy|grype|cosign|image.*scan|sign.*image', content, re.IGNORECASE):
                        has_supply_chain = True
                        break

    if not has_supply_chain:
        f(295, "Security", "medium", "backend", 0,
          "No supply chain security detected — container image scanning and "
          "signing required (Law 295).",
          "Implement supply chain security:\n"
          "  1. Scan images with Trivy/Grype in CI\n"
          "  2. Sign images with Cosign\n"
          "  3. Verify signatures on deploy\n"
          "  4. Block unsigned images")


# ══════════════════════════════════════════════════════════════
# SECTION 9: RESILIENCE (Laws 296-310)
# ══════════════════════════════════════════════════════════════

def check_section_resilience():
    """Laws 296-310: Resilience — circuit breaker, retry, DLQ, health, fallback."""
    _law_296_circuit_breaker()
    _law_297_retry_backoff()
    _law_298_dead_letter_queue()
    _law_299_feature_health()
    _law_300_feature_fallback()
    _law_301_error_budget()
    _law_302_on_call()
    _law_303_runbooks()
    _law_304_dr()
    _law_305_db_failover()
    _law_306_multi_region()
    _law_307_backup_verify()
    _law_308_drift_detection()
    _law_309_dep_monitoring()
    _law_310_post_incident()


def _law_296_circuit_breaker():
    """Law 296: All external calls wrapped."""
    # Check for circuit breaker patterns
    has_circuit_breaker = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'circuit.*breaker|CircuitBreaker|circuit_breaker|pybreaker|tenacity', content, re.IGNORECASE):
            has_circuit_breaker = True
            break

    # Check if external calls exist without circuit breaker
    has_external_calls = False
    for p in PROVIDERS:
        content = read(p)
        if re.search(r'requests\.|httpx\.|aiohttp\.|urllib', content):
            has_external_calls = True
            break

    if has_external_calls and not has_circuit_breaker:
        f(296, "Resilience", "high", "backend", 0,
          "External API calls detected without circuit breaker — all external "
          "calls must be wrapped with circuit breaker (Law 296).",
          "Add circuit breaker:\n"
          "  1. Use pybreaker or tenacity\n"
          "  2. Set failure_threshold=5, reset_timeout=60\n"
          "  3. Wrap all provider HTTP calls\n"
          "  4. Return fallback on open circuit")


def _law_297_retry_backoff():
    """Law 297: 1-2-4-8s. Jitter. Max 5."""
    # Check for retry patterns
    has_retry = False
    has_backoff = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'retry|Retry|RETRY', content):
            has_retry = True
        if re.search(r'backoff|exponential|jitter|sleep.*2\*\*', content, re.IGNORECASE):
            has_backoff = True

    if not has_retry:
        f(297, "Resilience", "medium", "backend", 0,
          "No retry pattern detected — transient failures must be retried with "
          "exponential backoff (1-2-4-8s) and jitter, max 5 attempts (Law 297).",
          "Implement retry with backoff:\n"
          "  1. Use tenacity: @retry(stop=stop_after_attempt(5))\n"
          "  2. Wait: wait_exponential(multiplier=1, max=8) + wait_random(0, 1)\n"
          "  3. Only retry on transient errors\n"
          "  4. Log retry attempts")


def _law_298_dead_letter_queue():
    """Law 298: Failed events to DLQ."""
    # Check for DLQ patterns
    has_dlq = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'dead.*letter|DLQ|dlq|failed.*queue|error.*queue', content, re.IGNORECASE):
            has_dlq = True
            break

    if not has_dlq:
        f(298, "Resilience", "medium", "backend", 0,
          "No dead letter queue detected — failed events must be routed to DLQ "
          "for later analysis and replay (Law 298).",
          "Implement DLQ:\n"
          "  1. Create DLQ topic/queue in message broker\n"
          "  2. Route failed events after max retries\n"
          "  3. Add DLQ monitoring and alerting\n"
          "  4. Implement replay mechanism")


def _law_299_feature_health():
    """Law 299: Per-feature in /health/deps."""
    # Check for health check endpoints
    has_health = False
    has_deps_health = False
    for p in ROUTERS:
        content = read(p)
        if re.search(r'health|healthz|readyz', content, re.IGNORECASE):
            has_health = True
        if re.search(r'health/deps|healthz/deps|/deps', content, re.IGNORECASE):
            has_deps_health = True

    if not has_health:
        f(299, "Resilience", "medium", "backend", 0,
          "No health check endpoint detected — /health endpoint required for "
          "liveness/readiness probes (Law 299).",
          "Add health endpoints:\n"
          "  GET /health — liveness (200 OK)\n"
          "  GET /health/ready — readiness (checks DB, Redis)\n"
          "  GET /health/deps — per-dependency status")

    if has_health and not has_deps_health:
        f(299, "Resilience", "low", "backend", 0,
          "Health endpoint exists but no per-feature dependency checks — "
          "/health/deps required for feature-level health (Law 299).",
          "Add per-feature health:\n"
          "  GET /health/deps — returns status of each dependency\n"
          "  Check: DB, Redis, external APIs, queues")


def _law_300_feature_fallback():
    """Law 300: Each feature defines degradation."""
    # Check for fallback patterns
    has_fallback = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'fallback|degrad|graceful|default.*response|cache.*stale', content, re.IGNORECASE):
            has_fallback = True
            break

    if not has_fallback:
        f(300, "Resilience", "medium", "backend", 0,
          "No feature fallback detected — each feature must define degradation "
          "behavior for when dependencies fail (Law 300).",
          "Implement feature fallbacks:\n"
          "  1. Define fallback for each external dependency\n"
          "  2. Use cached data when service unavailable\n"
          "  3. Return partial data with warnings\n"
          "  4. Document degradation behavior per feature")


def _law_301_error_budget():
    """Law 301: Exhaustion = freeze."""
    # Check for error budget tracking
    has_error_budget = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'error.*budget|SLO|SLA|budget.*exhaust|freeze.*deploy', content, re.IGNORECASE):
            has_error_budget = True
            break

    if not has_error_budget:
        f(301, "Resilience", "low", "backend", 0,
          "No error budget tracking detected — SLO-based error budget with "
          "deploy freeze on exhaustion required (Law 301).",
          "Implement error budget:\n"
          "  1. Define SLO per service (e.g., 99.9% availability)\n"
          "  2. Track error budget consumption\n"
          "  3. Freeze deploys when budget exhausted\n"
          "  4. Require SRE approval to override freeze")


def _law_302_on_call():
    """Law 302: PagerDuty/Opsgenie."""
    # Check for on-call configuration
    has_oncall = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'pagerduty|opsgenie|pager.*duty|on.call|oncall', content, re.IGNORECASE):
            has_oncall = True
            break

    if not has_oncall:
        f(302, "Resilience", "medium", "backend", 0,
          "No on-call configuration detected — PagerDuty/Opsgenie integration "
          "required for incident response (Law 302).",
          "Set up on-call:\n"
          "  1. Create PagerDuty/Opsgenie service\n"
          "  2. Define escalation policy\n"
          "  3. Route alerts to on-call engineer\n"
          "  4. Track response times")


def _law_303_runbooks():
    """Law 303: Per-alert. Tested quarterly."""
    # Check for runbooks
    has_runbooks = False
    runbook_paths = [
        ROOT.parent / "docs" / "runbooks",
        ROOT.parent / "docs" / "incident",
        ROOT.parent / "runbooks",
    ]
    for rp in runbook_paths:
        if rp.exists() and safe_rglob(rp):
            has_runbooks = True
            break

    if not has_runbooks:
        f(303, "Resilience", "low", "backend", 0,
          "No runbooks detected — per-alert runbooks tested quarterly required "
          "for incident response (Law 303).",
          "Create runbooks:\n"
          "  1. Document response steps per alert type\n"
          "  2. Store in docs/runbooks/\n"
          "  3. Test quarterly with game days\n"
          "  4. Update after each incident")


def _law_304_dr():
    """Law 304: RPO=5min, RTO=1hr."""
    # Check for DR configuration
    has_dr = False
    dr_paths = [
        ROOT.parent / "docs" / "dr",
        ROOT.parent / "docs" / "disaster-recovery",
    ]
    for dp in dr_paths:
        if dp.exists():
            has_dr = True
            break

    for p in ALL_PY:
        content = read(p)
        if re.search(r'RPO|RTO|disaster.*recover|recovery.*point|recovery.*time', content, re.IGNORECASE):
            has_dr = True
            break

    if not has_dr:
        f(304, "Resilience", "medium", "backend", 0,
          "No disaster recovery configuration detected — RPO=5min, RTO=1hr "
          "required for business continuity (Law 304).",
          "Implement DR:\n"
          "  1. Document DR plan with RPO=5min, RTO=1hr\n"
          "  2. Set up cross-region replication\n"
          "  3. Test failover quarterly\n"
          "  4. Automate recovery procedures")


def _law_305_db_failover():
    """Law 305: 30s promotion."""
    # Check for DB failover configuration
    has_failover = False
    for p in INFRA:
        content = read(p)
        if re.search(r'failover|promote|standby|replica.*promote', content, re.IGNORECASE):
            has_failover = True
            break

    if not has_failover:
        f(305, "Resilience", "medium", "backend", 0,
          "No DB failover configuration detected — automatic failover with "
          "30s promotion required for high availability (Law 305).",
          "Configure DB failover:\n"
          "  1. Use PostgreSQL streaming replication\n"
          "  2. Set up automatic failover (Patroni/repmgr)\n"
          "  3. Target promotion time < 30s\n"
          "  4. Test failover monthly")


def _law_306_multi_region():
    """Law 306: ≥2 regions."""
    # Check for multi-region configuration
    has_multi_region = False
    deploy_paths = [
        ROOT.parent / "docker-compose.prod.yml",
        ROOT.parent / "k8s",
        ROOT.parent / "terraform",
    ]
    for dp in deploy_paths:
        if dp.exists():
            if dp.is_dir():
                for p in safe_rglob(dp):
                    if p.is_file():
                        content = read(p)
                        if re.search(r'region|multi.*region|cross.*region', content, re.IGNORECASE):
                            has_multi_region = True
                            break
            else:
                content = read(dp)
                if re.search(r'region|multi.*region', content, re.IGNORECASE):
                    has_multi_region = True
                    break

    if not has_multi_region:
        f(306, "Resilience", "medium", "backend", 0,
          "No multi-region deployment detected — deployment in ≥2 regions "
          "required for regional failover (Law 306).",
          "Deploy multi-region:\n"
          "  1. Deploy to primary + secondary region\n"
          "  2. Set up cross-region DB replication\n"
          "  3. Use global load balancer\n"
          "  4. Test regional failover")


def _law_307_backup_verify():
    """Law 307: Daily restore test."""
    # Check for backup verification
    has_backup_verify = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'backup.*verify|verify.*backup|restore.*test|test.*restore', content, re.IGNORECASE):
            has_backup_verify = True
            break

    if not has_backup_verify:
        f(307, "Resilience", "medium", "backend", 0,
          "No backup verification detected — daily restore tests required "
          "to ensure backup integrity (Law 307).",
          "Implement backup verification:\n"
          "  1. Schedule daily automated restore tests\n"
          "  2. Verify data integrity after restore\n"
          "  3. Alert on restore failure\n"
          "  4. Document RTO/RPO validation")


def _law_308_drift_detection():
    """Law 308: IaC daily checks."""
    # Check for drift detection
    has_drift = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'drift.*detect|detect.*drift|iac.*check|terraform.*plan', content, re.IGNORECASE):
            has_drift = True
            break

    if not has_drift:
        f(308, "Resilience", "low", "backend", 0,
          "No drift detection detected — daily IaC drift checks required "
          "to prevent configuration drift (Law 308).",
          "Implement drift detection:\n"
          "  1. Run terraform plan daily in CI\n"
          "  2. Alert on detected drift\n"
          "  3. Auto-remediate or create ticket\n"
          "  4. Track drift history")


def _law_309_dep_monitoring():
    """Law 309: External status pages."""
    # Check for dependency monitoring
    has_dep_monitor = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'status.*page|uptime|dependency.*monitor|external.*health', content, re.IGNORECASE):
            has_dep_monitor = True
            break

    if not has_dep_monitor:
        f(309, "Resilience", "low", "backend", 0,
          "No dependency monitoring detected — external service status page "
          "monitoring required for dependency awareness (Law 309).",
          "Implement dependency monitoring:\n"
          "  1. Monitor status pages of critical dependencies\n"
          "  2. Use Better Uptime or StatusCake\n"
          "  3. Alert on dependency degradation\n"
          "  4. Document dependency impact")


def _law_310_post_incident():
    """Law 310: Blameless."""
    # Check for post-incident review process
    has_post_incident = False
    docs_paths = [
        ROOT.parent / "docs" / "incident",
        ROOT.parent / "docs" / "postmortem",
    ]
    for dp in docs_paths:
        if dp.exists():
            has_post_incident = True
            break

    for p in ALL_PY:
        content = read(p)
        if re.search(r'post.*incident|postmortem|blameless|incident.*review', content, re.IGNORECASE):
            has_post_incident = True
            break

    if not has_post_incident:
        f(310, "Resilience", "low", "backend", 0,
          "No post-incident review process detected — blameless post-incident "
          "reviews required for continuous improvement (Law 310).",
          "Implement post-incident reviews:\n"
          "  1. Create blameless postmortem template\n"
          "  2. Review within 48h of incident\n"
          "  3. Track action items to completion\n"
          "  4. Share learnings across teams")


# ══════════════════════════════════════════════════════════════
# SECTION 10: OPERATIONS (Laws 311-325)
# ══════════════════════════════════════════════════════════════

def check_section_operations():
    """Laws 311-325: Operations — feature flags, compliance, IaC, monitoring, access."""
    _law_311_feature_flags()
    _law_312_ab_testing()
    _law_313_compliance()
    _law_314_iac()
    _law_315_log_aggregation()
    _law_316_dashboards()
    _law_317_alerting_tiers()
    _law_318_capacity_planning()
    _law_319_release_mgmt()
    _law_320_devx()
    _law_321_doc_freshness()
    _law_322_cost_allocation()
    _law_323_human_access()
    _law_324_change_mgmt()
    _law_325_sustainability()


def _law_311_feature_flags():
    """Law 311: Gradual rollout."""
    # Check for feature flags
    has_feature_flags = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'feature.*flag|feature_flag|FeatureFlag|launchdarkly|split\.io', content, re.IGNORECASE):
            has_feature_flags = True
            break

    if not has_feature_flags:
        f(311, "Operations", "medium", "backend", 0,
          "No feature flag system detected — gradual rollout via feature flags "
          "required for safe deployments (Law 311).",
          "Implement feature flags:\n"
          "  1. Use LaunchDarkly, Split.io, or custom solution\n"
          "  2. Support percentage-based rollout\n"
          "  3. Enable instant rollback\n"
          "  4. Track flag usage and cleanup")


def _law_312_ab_testing():
    """Law 312: Hash-based. Sticky."""
    # Check for A/B testing
    has_ab_testing = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'a.b.*test|ab_test|experiment|variant.*hash|hash.*bucket', content, re.IGNORECASE):
            has_ab_testing = True
            break

    if not has_ab_testing:
        f(312, "Operations", "low", "backend", 0,
          "No A/B testing framework detected — hash-based sticky A/B testing "
          "required for data-driven decisions (Law 312).",
          "Implement A/B testing:\n"
          "  1. Use consistent hash for variant assignment\n"
          "  2. Ensure sticky assignments per user\n"
          "  3. Track experiment metrics\n"
          "  4. Support statistical significance testing")


def _law_313_compliance():
    """Law 313: GDPR. PCI-DSS."""
    # Check for compliance documentation
    has_compliance = False
    docs_paths = [
        ROOT.parent / "docs" / "compliance",
        ROOT.parent / "docs" / "gdpr",
        ROOT.parent / "docs" / "pci",
    ]
    for dp in docs_paths:
        if dp.exists():
            has_compliance = True
            break

    for p in ALL_PY:
        content = read(p)
        if re.search(r'GDPR|PCI.DSS|pci.dss|data.*protection|right.*forget|data.*retention', content, re.IGNORECASE):
            has_compliance = True
            break

    if not has_compliance:
        f(313, "Operations", "high", "backend", 0,
          "No compliance documentation detected — GDPR and PCI-DSS compliance "
          "documentation required for legal operation (Law 313).",
          "Document compliance:\n"
          "  1. Create GDPR compliance doc (data mapping, DPA)\n"
          "  2. Create PCI-DSS compliance doc (scope, controls)\n"
          "  3. Implement data retention policies\n"
          "  4. Add right-to-erasure endpoint")


def _law_314_iac():
    """Law 314: Terraform/Pulumi."""
    # Check for IaC configuration
    has_iac = False
    iac_paths = [
        ROOT.parent / "terraform",
        ROOT.parent / "pulumi",
        ROOT.parent / "infrastructure" / "terraform",
    ]
    for ip in iac_paths:
        if ip.exists():
            has_iac = True
            break

    if not has_iac:
        f(314, "Operations", "medium", "backend", 0,
          "No Infrastructure as Code detected — Terraform or Pulumi required "
          "for reproducible infrastructure (Law 314).",
          "Implement IaC:\n"
          "  1. Define all infrastructure in Terraform/Pulumi\n"
          "  2. Store state remotely (S3 + DynamoDB)\n"
          "  3. Use CI/CD for infrastructure changes\n"
          "  4. Implement plan/apply workflow")


def _law_315_log_aggregation():
    """Law 315: ELK/Loki."""
    # Check for log aggregation
    has_log_agg = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'elasticsearch.*log|loki|logstash|kibana|ELK|graylog|fluentd', content, re.IGNORECASE):
            has_log_agg = True
            break

    if not has_log_agg:
        f(315, "Operations", "medium", "backend", 0,
          "No log aggregation detected — ELK stack or Loki required for "
          "centralized log management (Law 315).",
          "Implement log aggregation:\n"
          "  1. Deploy ELK stack or Grafana Loki\n"
          "  2. Configure structured JSON logging\n"
          "  3. Add trace ID correlation\n"
          "  4. Set up log retention policies")


def _law_316_dashboards():
    """Law 316: Grafana."""
    # Check for dashboard configuration
    has_dashboards = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'grafana|dashboard|prometheus.*metric|metric.*export', content, re.IGNORECASE):
            has_dashboards = True
            break

    if not has_dashboards:
        f(316, "Operations", "medium", "backend", 0,
          "No dashboard configuration detected — Grafana dashboards required "
          "for operational visibility (Law 316).",
          "Implement dashboards:\n"
          "  1. Deploy Grafana with Prometheus\n"
          "  2. Create service-level dashboards\n"
          "  3. Track RED metrics (Rate, Errors, Duration)\n"
          "  4. Add business metrics dashboards")


def _law_317_alerting_tiers():
    """Law 317: P1/P2/P3."""
    # Check for alerting tiers
    has_alerting = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'P1|P2|P3|severity.*critical|severity.*warning|alert.*tier', content, re.IGNORECASE):
            has_alerting = True
            break

    if not has_alerting:
        f(317, "Operations", "medium", "backend", 0,
          "No alerting tiers detected — P1/P2/P3 alerting classification "
          "required for appropriate incident response (Law 317).",
          "Implement alerting tiers:\n"
          "  P1: Service down → page immediately\n"
          "  P2: Degraded → page during business hours\n"
          "  P3: Warning → ticket, next business day\n"
          "  Define escalation per tier")


def _law_318_capacity_planning():
    """Law 318: Monthly."""
    # Check for capacity planning
    has_capacity = False
    docs_paths = [
        ROOT.parent / "docs" / "capacity",
        ROOT.parent / "docs" / "planning",
    ]
    for dp in docs_paths:
        if dp.exists():
            has_capacity = True
            break

    for p in ALL_PY:
        content = read(p)
        if re.search(r'capacity.*plan|growth.*project|resource.*forecast', content, re.IGNORECASE):
            has_capacity = True
            break

    if not has_capacity:
        f(318, "Operations", "low", "backend", 0,
          "No capacity planning detected — monthly capacity planning required "
          "for proactive resource management (Law 318).",
          "Implement capacity planning:\n"
          "  1. Monthly resource utilization review\n"
          "  2. Project growth trends\n"
          "  3. Plan scaling actions\n"
          "  4. Budget forecasting")


def _law_319_release_mgmt():
    """Law 319: Canary → full."""
    # Check for release management
    has_release_mgmt = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'canary|blue.*green|rolling.*deploy|deploy.*strategy', content, re.IGNORECASE):
            has_release_mgmt = True
            break

    if not has_release_mgmt:
        f(319, "Operations", "medium", "backend", 0,
          "No release management strategy detected — canary → full rollout "
          "required for safe deployments (Law 319).",
          "Implement release management:\n"
          "  1. Deploy to canary (5% traffic)\n"
          "  2: Monitor error rate and latency\n"
          "  3. Gradually increase to 100%\n"
          "  4. Auto-rollback on error threshold")


def _law_320_devx():
    """Law 320: < 10min setup."""
    # Check for developer setup documentation
    has_devx = False
    setup_paths = [
        ROOT.parent / "Makefile",
        ROOT.parent / "docker-compose.yml",
        ROOT.parent / "CONTRIBUTING.md",
        ROOT.parent / "docs" / "setup.md",
    ]
    for sp in setup_paths:
        if sp.exists():
            has_devx = True
            break

    if not has_devx:
        f(320, "Operations", "low", "backend", 0,
          "No developer setup documentation detected — < 10min setup required "
          "for developer productivity (Law 320).",
          "Improve DevX:\n"
          "  1. Create one-command setup: 'make dev'\n"
          "  2. Use Docker Compose for dependencies\n"
          "  3. Document setup in CONTRIBUTING.md\n"
          "  4. Target < 10min from clone to running")


def _law_321_doc_freshness():
    """Law 321: Quarterly reviews."""
    # Check for documentation review process
    has_doc_review = False
    docs_paths = [
        ROOT.parent / "docs",
    ]
    for dp in docs_paths:
        if dp.exists():
            for p in safe_rglob(dp):
                if p.is_file():
                    content = read(p)
                    if re.search(r'review.*quarter|quarter.*review|doc.*fresh|last.*reviewed', content, re.IGNORECASE):
                        has_doc_review = True
                        break

    if not has_doc_review:
        f(321, "Operations", "low", "backend", 0,
          "No documentation review process detected — quarterly doc reviews "
          "required for documentation freshness (Law 321).",
          "Implement doc reviews:\n"
          "  1. Add 'last_reviewed' date to docs\n"
          "  2. Schedule quarterly review\n"
          "  3. Track stale docs (> 90 days)\n"
          "  4. Assign doc owners per section")


def _law_322_cost_allocation():
    """Law 322: By domain/team."""
    # Check for cost allocation
    has_cost_alloc = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'cost.*alloc|alloc.*cost|tag.*cost|cost.*center|team.*budget', content, re.IGNORECASE):
            has_cost_alloc = True
            break

    if not has_cost_alloc:
        f(322, "Operations", "low", "backend", 0,
          "No cost allocation detected — cost allocation by domain/team "
          "required for financial accountability (Law 322).",
          "Implement cost allocation:\n"
          "  1. Tag all resources with domain/team\n"
          "  2. Use cloud cost allocation tags\n"
          "  3. Generate monthly cost reports\n"
          "  4. Set budget alerts per team")


def _law_323_human_access():
    """Law 323: Least-privilege. 24h offboarding."""
    # Check for access control
    has_access_control = False
    for p in RBAC:
        content = read(p)
        if re.search(r'least.*privilege|offboarding|access.*revoke|deprovision', content, re.IGNORECASE):
            has_access_control = True
            break

    if not has_access_control:
        f(323, "Operations", "high", "backend", 0,
          "No access control process detected — least-privilege access with "
          "24h offboarding required for security (Law 323).",
          "Implement access control:\n"
          "  1. Define least-privilege roles in RBAC\n"
          "  2. Automate access provisioning/deprovisioning\n"
          "  3. Complete offboarding within 24h\n"
          "  4. Quarterly access reviews")


def _law_324_change_mgmt():
    """Law 324: All via PR + CI."""
    # Check for change management
    has_change_mgmt = False
    ci_paths = [
        ROOT.parent / ".github" / "workflows",
    ]
    for cp in ci_paths:
        if cp.exists():
            for p in safe_rglob(cp):
                if p.is_file():
                    content = read(p)
                    if re.search(r'require.*review|branch.*protect|PR.*required|pull_request', content, re.IGNORECASE):
                        has_change_mgmt = True
                        break

    if not has_change_mgmt:
        f(324, "Operations", "medium", "backend", 0,
          "No change management enforcement detected — all changes via PR + CI "
          "required for quality control (Law 324).",
          "Implement change management:\n"
          "  1. Require PR review before merge\n"
          "  2. Enforce CI pass before merge\n"
          "  3. Protect main branch\n"
          "  4. Require PR for infrastructure changes")


def _law_325_sustainability():
    """Law 325: Right-size. Carbon tracking."""
    # Check for sustainability practices
    has_sustainability = False
    for p in ALL_PY:
        content = read(p)
        if re.search(r'carbon|sustain|green.*computing|energy.*efficien|right.*size', content, re.IGNORECASE):
            has_sustainability = True
            break

    if not has_sustainability:
        f(325, "Operations", "low", "backend", 0,
          "No sustainability practices detected — right-sizing and carbon "
          "tracking required for environmental responsibility (Law 325).",
          "Implement sustainability:\n"
          "  1. Right-size instances based on actual usage\n"
          "  2. Track carbon footprint (cloud provider tools)\n"
          "  3. Use spot instances for batch workloads\n"
          "  4. Set sustainability goals and track progress")
