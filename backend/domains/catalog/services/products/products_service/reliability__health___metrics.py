# === RELIABILITY: Health & Metrics ===


def get_products_health() -> dict:
    """Return health status of the products service for monitoring."""
    from infrastructure.database.database import check_connection_health, get_pool_metrics

    db_healthy = check_connection_health()
    pool_metrics = get_pool_metrics()

    return {
        "database": "healthy" if db_healthy else "unhealthy",
        "connection_pool": pool_metrics,
        "cache_version": _get_product_cache_version(),
    }