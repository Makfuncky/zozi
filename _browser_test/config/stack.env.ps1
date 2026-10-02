# Real secrets injected from project .env for local Playwright runs.
# WARNING: DO NOT commit this file. Ensure it is ignored by git.

$env:APP_ENV = 'development'

$env:BACKEND_URL = 'http://127.0.0.1:8000'
$env:FRONTEND_URL = 'http://127.0.0.1:3100'

$env:DATABASE_URL = 'postgresql://neondb_owner:npg_pnTuMIq7h9Es@ep-sparkling-dream-za50z6c0-pooler.c-2.eu-west-2.aws.neon.tech/neondb'

$env:SECRET_KEY = 'K1shXALnoZnJzgvaq5DIwh9SWXWPX1YGNi5cY97jjTM2cFN4I9F6jWXVITL9fgKW'

$env:CELERY_BROKER_URL = 'valkey://localhost:6379/0'

$env:STORAGE_BACKEND = 'local'
$env:S3_BUCKET = 'zozi-media'
$env:S3_ACCESS_KEY_ID = 'dummy_access_key'
$env:S3_SECRET_ACCESS_KEY = 'dummy_secret_key'

$env:PW_WORKERS = '1'
$env:PW_TIMEOUT = '30000'
