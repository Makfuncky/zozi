#!/bin/bash

# ZOZI Marketplace Deployment Script
# Usage: ./deploy.sh [environment] [platform]
# Example: ./deploy.sh production aws

set -e

ENVIRONMENT=${1:-development}
PLATFORM=${2:-docker}
COMPOSE_FILE=${ZOZI_COMPOSE_FILE:-}
HEALTHCHECK_URL=${ZOZI_HEALTHCHECK_URL:-}
HEALTHCHECK_ATTEMPTS=${ZOZI_HEALTHCHECK_ATTEMPTS:-20}
HEALTHCHECK_DELAY_SECONDS=${ZOZI_HEALTHCHECK_DELAY_SECONDS:-5}

compose_cmd() {
    if [ -n "$COMPOSE_FILE" ]; then
        docker-compose -f "$COMPOSE_FILE" "$@"
    else
        docker-compose "$@"
    fi
}

resolve_healthcheck_url() {
    if [ -n "$HEALTHCHECK_URL" ]; then
        echo "$HEALTHCHECK_URL"
        return
    fi

    if [ "$ENVIRONMENT" = "production" ]; then
        echo "http://localhost/health/ready"
    else
        echo "http://localhost:8000/health/ready"
    fi
}

wait_for_healthcheck() {
    local url
    url=$(resolve_healthcheck_url)
    local attempt=1

    echo "🔎 Waiting for health check at $url"
    while [ "$attempt" -le "$HEALTHCHECK_ATTEMPTS" ]; do
        if curl -fsS "$url" >/dev/null 2>&1; then
            echo "✅ Health check passed"
            return 0
        fi
        echo "⏳ Health check attempt $attempt/$HEALTHCHECK_ATTEMPTS failed"
        attempt=$((attempt + 1))
        sleep "$HEALTHCHECK_DELAY_SECONDS"
    done

    return 1
}

rollback_docker_release() {
    local previous_ref=$1

    echo "↩️ Rolling back to $previous_ref"
    git checkout --detach "$previous_ref"
    compose_cmd down
    compose_cmd pull || true
    compose_cmd up -d --build
    run_docker_migrations
}

run_docker_migrations() {
    echo "🗄️ Applying database migrations (alembic upgrade head)"
    compose_cmd exec -T backend alembic upgrade head
}

echo "🚀 Deploying ZOZI Marketplace to $ENVIRONMENT on $PLATFORM"

# Load environment variables
if [ -f ".env.$ENVIRONMENT" ]; then
    export $(cat .env.$ENVIRONMENT | xargs)
fi

case $PLATFORM in
    "docker")
        echo "🐳 Deploying with Docker Compose"
        PREVIOUS_REF=$(git rev-parse HEAD 2>/dev/null || echo "")
        if [ "$ENVIRONMENT" = "production" ]; then
            if [ -z "$COMPOSE_FILE" ]; then
                COMPOSE_FILE="docker-compose.prod.yml"
            fi
            git fetch origin main
            git pull --ff-only origin main
        else
            git pull --ff-only origin "$(git rev-parse --abbrev-ref HEAD)" || true
        fi

        compose_cmd down
        compose_cmd pull || true
        compose_cmd up -d --build
        run_docker_migrations

        if ! wait_for_healthcheck; then
            echo "❌ Deployment health gate failed"
            if [ -n "$PREVIOUS_REF" ]; then
                rollback_docker_release "$PREVIOUS_REF"
            fi
            exit 1
        fi
        ;;

    "aws")
        echo "☁️ Deploying to AWS"
        # AWS ECS deployment
        aws ecs update-service --cluster zozi-cluster --service zozi-service --force-new-deployment
        ;;

    "vercel")
        echo "▲ Deploying frontend to Vercel"
        cd frontend/web_app
        vercel --prod
        cd ../..
        ;;

    "railway")
        echo "🚂 Deploying to Railway"
        railway up
        ;;

    *)
        echo "❌ Unsupported platform: $PLATFORM"
        echo "Supported platforms: docker, aws, vercel, railway"
        exit 1
        ;;
esac

echo "✅ Deployment completed successfully!"