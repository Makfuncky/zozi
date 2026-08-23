"""controllers.comms.chatbot_controller controller.

Business logic is delegated to services.comms.chatbot_service (routers -> controllers -> services)."""

from domains.comms.services.autobot.chatbot_service import _INTENT_PATTERNS
from domains.comms.services.autobot.chatbot_service import _NOISE_IN_PRODUCT
from domains.comms.services.autobot.chatbot_service import _PRODUCT_REFERENCE_HINT
from domains.comms.services.autobot.chatbot_service import _PRODUCT_REQUEST_HINT
from domains.comms.services.autobot.chatbot_service import _SEARCH_STOPWORDS
from domains.comms.services.autobot.chatbot_service import _SESSION_HISTORY
from domains.comms.services.autobot.chatbot_service import _SESSION_MAX_MESSAGES
from domains.comms.services.autobot.chatbot_service import _SESSION_TTL
from domains.comms.services.autobot.chatbot_service import _STATIC_REPLIES
from domains.comms.services.autobot.chatbot_service import _STATIC_REPLIES_AR
from domains.comms.services.autobot.chatbot_service import _alternative_results_reply
from domains.comms.services.autobot.chatbot_service import _append_to_session
from domains.comms.services.autobot.chatbot_service import _build_follow_up_prompts
from domains.comms.services.autobot.chatbot_service import _build_relaxed_product_recommendations
from domains.comms.services.autobot.chatbot_service import _catalog_guidance_reply
from domains.comms.services.autobot.chatbot_service import _category_sales_line
from domains.comms.services.autobot.chatbot_service import _classify_intent
from domains.comms.services.autobot.chatbot_service import _extract_max_price
from domains.comms.services.autobot.chatbot_service import _extract_search_keywords
from domains.comms.services.autobot.chatbot_service import _format_price_value
from domains.comms.services.autobot.chatbot_service import _get_or_create_session
from domains.comms.services.autobot.chatbot_service import _last_product_filters
from domains.comms.services.autobot.chatbot_service import _lead_product_line
from domains.comms.services.autobot.chatbot_service import _load_browsing_history
from domains.comms.services.autobot.chatbot_service import _merge_product_filters
from domains.comms.services.autobot.chatbot_service import _price_badge
from domains.comms.services.autobot.chatbot_service import _price_proximity_score
from domains.comms.services.autobot.chatbot_service import _product_constraints
from domains.comms.services.autobot.chatbot_service import _product_results_reply
from domains.comms.services.autobot.chatbot_service import _product_subject
from domains.comms.services.autobot.chatbot_service import _profile_personalization_hint
from domains.comms.services.autobot.chatbot_service import _record_chatbot_event
from domains.comms.services.autobot.chatbot_service import _result_guidance_line
from domains.comms.services.autobot.chatbot_service import _rounded_budget_prompt
from domains.comms.services.autobot.chatbot_service import _safe_json_dumps
from domains.comms.services.autobot.chatbot_service import _search_tokens
from domains.comms.services.autobot.chatbot_service import _serialize_products
from domains.comms.services.autobot.chatbot_service import _should_merge_product_filters
from domains.comms.services.autobot.chatbot_service import _should_treat_as_product_search
from domains.comms.services.autobot.chatbot_service import _static_reply
from domains.comms.services.autobot.chatbot_service import _style_reference_terms
from domains.comms.services.autobot.chatbot_service import _style_similarity_score
from domains.comms.services.autobot.chatbot_service import _top_counter_values
from domains.comms.services.autobot.chatbot_service import _upsell_hint
from domains.comms.services.autobot.chatbot_service import get_shopper_profile
from domains.comms.services.autobot.chatbot_service import handle_message
from domains.comms.services.autobot.chatbot_service import logger
from domains.comms.services.autobot.chatbot_service import record_product_click
from domains.comms.services.autobot.chatbot_service import record_product_view
from domains.comms.services.autobot.chatbot_service import search_products
from domains.comms.services.autobot.chatbot_service import search_products_with_context

__all__ = [
    "_INTENT_PATTERNS", "_NOISE_IN_PRODUCT", "_PRODUCT_REFERENCE_HINT", "_PRODUCT_REQUEST_HINT", "_SEARCH_STOPWORDS", "_SESSION_HISTORY",
    "_SESSION_MAX_MESSAGES", "_SESSION_TTL", "_STATIC_REPLIES", "_STATIC_REPLIES_AR", "_alternative_results_reply", "_append_to_session",
    "_build_follow_up_prompts", "_build_relaxed_product_recommendations", "_catalog_guidance_reply", "_category_sales_line", "_classify_intent", "_extract_max_price",
    "_extract_search_keywords", "_format_price_value", "_get_or_create_session", "_last_product_filters", "_lead_product_line", "_load_browsing_history",
    "_merge_product_filters", "_price_badge", "_price_proximity_score", "_product_constraints", "_product_results_reply", "_product_subject",
    "_profile_personalization_hint", "_record_chatbot_event", "_result_guidance_line", "_rounded_budget_prompt", "_safe_json_dumps", "_search_tokens",
    "_serialize_products", "_should_merge_product_filters", "_should_treat_as_product_search", "_static_reply", "_style_reference_terms", "_style_similarity_score",
    "_top_counter_values", "_upsell_hint", "get_shopper_profile", "handle_message", "logger", "record_product_click",
    "record_product_view", "search_products", "search_products_with_context"
]
