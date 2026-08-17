"""controllers.comms.chatbot_controller controller.

Business logic is delegated to services.comms.chatbot_service (routers -> controllers -> services)."""

from services.comms.chatbot_service import (
    _INTENT_PATTERNS, _NOISE_IN_PRODUCT, _PRODUCT_REFERENCE_HINT, _PRODUCT_REQUEST_HINT, _SEARCH_STOPWORDS, _SESSION_HISTORY,
    _SESSION_MAX_MESSAGES, _SESSION_TTL, _STATIC_REPLIES, _STATIC_REPLIES_AR, _alternative_results_reply, _append_to_session,
    _build_follow_up_prompts, _build_relaxed_product_recommendations, _catalog_guidance_reply, _category_sales_line, _classify_intent, _extract_max_price,
    _extract_search_keywords, _format_price_value, _get_or_create_session, _last_product_filters, _lead_product_line, _load_browsing_history,
    _merge_product_filters, _price_badge, _price_proximity_score, _product_constraints, _product_results_reply, _product_subject,
    _profile_personalization_hint, _record_chatbot_event, _result_guidance_line, _rounded_budget_prompt, _safe_json_dumps, _search_tokens,
    _serialize_products, _should_merge_product_filters, _should_treat_as_product_search, _static_reply, _style_reference_terms, _style_similarity_score,
    _top_counter_values, _upsell_hint, get_shopper_profile, handle_message, logger, record_product_click,
    record_product_view, search_products, search_products_with_context
)

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
