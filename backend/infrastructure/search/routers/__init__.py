"""Search routers package — re-exports the search controller surface."""

from infrastructure.search.routers.search_controller import (  # noqa: F401
    get_recommendations,
    smart_search,
)
