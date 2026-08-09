"""
MCP Server for Zozi AI Providers
==================================
Exposes all AI providers as MCP tools that any LLM (Claude, ChatGPT, etc.)
can call via the Model Context Protocol.

Run:
    python mcp_server.py

Or with SSE transport for production:
    python mcp_server.py --transport sse --port 8001

Test:
    python mcp_client_example.py
"""
from __future__ import annotations

import base64
import io
import json
import logging
import os
import sys
from typing import Any, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Create MCP server
mcp = FastMCP(
    "Zozi AI Providers",
    dependencies=[],
)

# Note: description is set via tool docstrings rather than FastMCP constructor
# in this version of the MCP SDK.


# ============================================================================
# 1. BG REMOVAL TOOLS
# ============================================================================

@mcp.tool(
    name="remove_background",
    description="Remove background from a product image. Accepts image bytes "
                "and returns processed PNG bytes. Supports multiple strategies: "
                "clean_commercial, precision_geometry, production_birefnet, etc.",
)
def remove_background_tool(
    image_b64: str,
    strategy: str = "general",
    model: Optional[str] = None,
) -> str:
    """Remove background from an image using AI.

    Args:
        image_b64: Base64-encoded image bytes (JPEG, PNG, WebP).
        strategy: Processing strategy (general, clean_commercial, precision_geometry,
                 production_birefnet, ultimate_v11, ultimate_v12, variant_testing).
        model: Optional specific rembg model name.

    Returns:
        Processed PNG bytes with transparent background.
    """
    from providers.bg_remover import remove_background
    image_bytes = base64.b64decode(image_b64)
    result = remove_background(image_bytes, model=model, strategy=strategy)
    return base64.b64encode(result).decode("utf-8")


@mcp.tool(
    name="magic_erase",
    description="Erase specific regions from an image using a mask.",
)
def magic_erase_tool(image_b64: str, mask_json: str) -> str:
    """Erase regions specified by a mask from an image.

    Args:
        image_bytes: Raw image bytes.
        mask_json: JSON string of a 2D array (H x W) with 255 for regions to erase, 0 to keep.

    Returns:
        Processed bytes with erased regions transparent.
    """
    import numpy as np
    from providers.bg_remover import magic_erase
    image_bytes = base64.b64decode(image_b64)
    mask_data = json.loads(mask_json)
    mask = np.array(mask_data, dtype=np.uint8)
    result = magic_erase(image_bytes, mask)
    return base64.b64encode(result).decode("utf-8")


# ============================================================================
# 2. VISION TOOLS
# ============================================================================

@mcp.tool(
    name="analyze_product_image",
    description="Analyze a product image and extract structured data: "
                "name, category, tags, colors, materials, variants, description, "
                "and product type classification.",
)
def analyze_product_image_tool(
    image_b64: str,
    filename: str = "",
    generate_copy: bool = False,
    subcategory: str = "",
) -> str:
    """Analyze a product image and return structured product data.

    Args:
        image_b64: Base64-encoded image bytes.
        filename: Optional filename hint.
        generate_copy: Whether to generate marketing copy.
        subcategory: Optional subcategory hint.

    Returns:
        JSON string with analysis results.
    """
    from providers.vision import analyze_product_image
    image_bytes = base64.b64decode(image_b64)
    result = analyze_product_image(
        image_bytes,
        filename=filename,
        generate_copy=generate_copy,
        use_vision=True,
        subcategory=subcategory,
    )
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp.tool(
    name="classify_product_type",
    description="Classify a product into a type (clothing, electronic, jewelry, etc.) "
                "based on its name, category, and subcategory.",
)
def classify_product_type_tool(
    product_name: str,
    category: str,
    subcategory: str = "",
) -> str:
    """Classify product type from metadata.

    Args:
        product_name: Product name.
        category: Product category.
        subcategory: Optional subcategory.

    Returns:
        Product type string (clothing, electronic, furniture, jewelry, etc.).
    """
    from providers.vision import classify_product_type
    return classify_product_type(product_name, category, subcategory)


@mcp.tool(
    name="normalize_category",
    description="Normalize a product name/description into a standard category "
                "(electronics, fashion, home, beauty, jewelry, sports, etc.).",
)
def normalize_category_tool(
    product_name: str,
    description: str = "",
) -> str:
    """Normalize product category from text.

    Args:
        product_name: Product name.
        description: Product description.

    Returns:
        Normalized category string.
    """
    from providers.vision import normalize_category
    return normalize_category(product_name, description)


@mcp.tool(
    name="suggest_price",
    description="Suggest a retail price for a product based on image, name, and category. "
                "Falls back to auto-pricing by product type when Ollama is unavailable.",
)
def suggest_price_tool(
    image_b64: str,
    product_name: str = "",
    category: str = "",
) -> str:
    """Suggest a price for a product.

    Args:
        image_b64: Base64-encoded product image bytes.
        product_name: Product name.
        category: Product category.

    Returns:
        JSON string with suggested_price, confidence, and reasoning.
    """
    from providers.vision import suggest_price
    image_bytes = base64.b64decode(image_b64)
    result = suggest_price(image_bytes, product_name=product_name, category=category)
    return json.dumps(result)


# ============================================================================
# 3. TEXT / EMBEDDING TOOLS
# ============================================================================

@mcp.tool(
    name="embed_text",
    description="Generate an embedding vector for a text string using Ollama's "
                "nomic-embed-text model. Returns a list of floats.",
)
def embed_text_tool(text: str) -> str:
    """Generate embedding vector for text.

    Args:
        text: Text to embed.

    Returns:
        JSON string of embedding vector (list of floats).
    """
    from providers.text import embed_text
    result = embed_text(text)
    return json.dumps(result)


@mcp.tool(
    name="cosine_similarity",
    description="Compute cosine similarity between two embedding vectors. "
                "Returns a score between 0 and 1.",
)
def cosine_similarity_tool(vector_a_json: str, vector_b_json: str) -> float:
    """Compute cosine similarity between two vectors.

    Args:
        vector_a_json: JSON string of first vector.
        vector_b_json: JSON string of second vector.

    Returns:
        Cosine similarity score (0-1).
    """
    from providers.text import cosine_similarity
    a = json.loads(vector_a_json)
    b = json.loads(vector_b_json)
    return cosine_similarity(a, b)


@mcp.tool(
    name="transcribe_audio",
    description="Transcribe audio bytes to text using Ollama whisper or "
                "SpeechRecognition fallback.",
)
def transcribe_audio_tool(audio_b64: str) -> str:
    """Transcribe audio to text.

    Args:
        audio_b64: Base64-encoded audio bytes (WAV, MP3, etc.).

    Returns:
        Transcribed text string.
    """
    from providers.text import transcribe_audio
    audio_bytes = base64.b64decode(audio_b64)
    return transcribe_audio(audio_bytes)


# ============================================================================
# 4. SEARCH TOOLS
# ============================================================================

@mcp.tool(
    name="search_products",
    description="Parse a natural language search query and return structured "
                "search parameters (price range, category, color, size, sort, etc.). "
                "Supports vector embedding search when a catalog is loaded.",
)
def search_products_tool(
    query: str,
    limit: int = 20,
) -> str:
    """Parse and execute a product search query.

    Args:
        query: Natural language query (e.g., 'blue shoes under $50').
        limit: Maximum results.

    Returns:
        JSON string with parsed query and search results.
    """
    from providers.search import AdvancedSearchEngine
    engine = AdvancedSearchEngine()
    result = engine.search(query, limit=limit)
    return json.dumps(result, default=str)


@mcp.tool(
    name="parse_search_query",
    description="Parse a natural language search query into structured filters "
                "without executing the search. Returns price range, category, "
                "color, size, sort, and search terms.",
)
def parse_search_query_tool(query: str) -> str:
    """Parse a search query into structured parameters.

    Args:
        query: Natural language query.

    Returns:
        JSON string with parsed query parameters.
    """
    from providers.search import AdvancedSearchEngine
    engine = AdvancedSearchEngine()
    result = engine.parse_query(query)
    return json.dumps(result)


# ============================================================================
# 5. CHATBOT TOOLS
# ============================================================================

@mcp.tool(
    name="chatbot_query",
    description="Process a customer support query through the Zozi chatbot. "
                "Supports: product_search, order_status, shipping, return, "
                "payment, account, help, greeting, and general intents.",
)
def chatbot_query_tool(
    query: str,
    session_id: str = "default",
) -> str:
    """Process a chatbot query and return a response.

    Args:
        query: User's message.
        session_id: Optional session identifier for conversation continuity.

    Returns:
        JSON string with response, intent, and session_id.
    """
    from providers.chatbot import ChatbotProvider
    bot = ChatbotProvider()
    result = bot.process_query(query, session_id=session_id)
    return json.dumps(result)


# ============================================================================
# 6. OCR TOOLS
# ============================================================================

@mcp.tool(
    name="parse_bill",
    description="Parse a bill or receipt image and extract structured fields: "
                "vendor, date, total, subtotal, tax, items, payment method.",
)
def parse_bill_tool(image_b64: str) -> str:
    """Parse a bill/receipt image.

    Args:
        image_b64: Base64-encoded image bytes of a bill or receipt.

    Returns:
        JSON string with extracted bill fields.
    """
    from providers.ocr import parse_bill_text
    image_bytes = base64.b64decode(image_b64)
    result = parse_bill_text(image_bytes)
    return json.dumps(result, default=str)


@mcp.tool(
    name="parse_statement_csv",
    description="Parse a financial statement CSV and extract structured data: "
                "rows, columns, total, and summary statistics.",
)
def parse_statement_csv_tool(csv_b64: str) -> str:
    """Parse a CSV financial statement.

    Args:
        csv_b64: Base64-encoded CSV file bytes.

    Returns:
        JSON string with parsed statement data.
    """
    from providers.ocr import parse_statement_csv
    csv_bytes = base64.b64decode(csv_b64)
    result = parse_statement_csv(csv_bytes)
    return json.dumps(result, default=str)


# ============================================================================
# 7. GEO / COUNTRY TOOLS
# ============================================================================

@mcp.tool(
    name="detect_country_from_ip",
    description="Detect a user's country from their IP address using headers. "
                "Supports X-Forwarded-For, X-Real-IP, CF-Connecting-IP.",
)
def detect_country_from_ip_tool(
    headers_json: str,
    client_host: Optional[str] = None,
) -> str:
    """Detect country from IP address.

    Args:
        headers_json: JSON string of HTTP request headers.
        client_host: Direct client IP if headers unavailable.

    Returns:
        JSON string with country_code and source.
    """
    from providers.geo import CountryDetectionProvider
    provider = CountryDetectionProvider()
    headers = json.loads(headers_json)
    code, source = provider.detect_country_from_ip(headers, client_host)
    return json.dumps({"country_code": code, "source": source})


@mcp.tool(
    name="search_country",
    description="Search for countries by name, code, capital, or region. "
                "Returns match details including currency, phone code, languages.",
)
def search_country_tool(query: str) -> str:
    """Search for countries matching a query.

    Args:
        query: Search query (country name, code, region, capital).

    Returns:
        JSON string of matching country details.
    """
    from providers.country import CountrySearchProvider
    provider = CountrySearchProvider()
    results = provider.search_country(query)
    return json.dumps(results)


@mcp.tool(
    name="get_country_details",
    description="Get detailed information about a country by ISO code: "
                "name, capital, currency, region, languages, phone code.",
)
def get_country_details_tool(country_code: str) -> str:
    """Get country details by ISO code.

    Args:
        country_code: ISO 3166-1 alpha-2 country code (e.g., 'US', 'AE', 'SA').

    Returns:
        JSON string with country details.
    """
    from providers.country import CountrySearchProvider
    provider = CountrySearchProvider()
    result = provider.get_country_details(country_code.upper())
    return json.dumps(result)


@mcp.tool(
    name="resolve_ip_location",
    description="Resolve an IP address to location data: country, region, city, "
                "latitude, longitude, and ISP.",
)
def resolve_ip_location_tool(ip: str) -> str:
    """Resolve IP address to location data.

    Args:
        ip: IP address string.

    Returns:
        JSON string with location details.
    """
    from providers.map import LocationProvider
    provider = LocationProvider()
    result = provider.resolve_ip(ip)
    return json.dumps(result)


@mcp.tool(
    name="calculate_distance",
    description="Calculate the distance between two coordinates using the "
                "Haversine formula. Returns distance in kilometers.",
)
def calculate_distance_tool(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
) -> float:
    """Calculate distance between two points.

    Args:
        lat1: Latitude of first point.
        lon1: Longitude of first point.
        lat2: Latitude of second point.
        lon2: Longitude of second point.

    Returns:
        Distance in kilometers.
    """
    from providers.map import LocationProvider
    provider = LocationProvider()
    return provider.calculate_distance(lat1, lon1, lat2, lon2)


# ============================================================================
# 8. FINANCE TOOLS
# ============================================================================

@mcp.tool(
    name="parse_email_to_ledger",
    description="Parse an email body into structured ledger entries: "
                "extracts dates, amounts, descriptions, and categories.",
)
def parse_email_to_ledger_tool(email_text: str) -> str:
    """Parse email to ledger entries.

    Args:
        email_text: Raw email body text.

    Returns:
        JSON string with ledger entries and metadata.
    """
    from providers.finance_ai import parse_email_to_ledger
    result = parse_email_to_ledger(email_text)
    return json.dumps({
        "success": result.success,
        "operation": result.operation,
        "data": result.data,
        "confidence": result.confidence,
        "error": result.error,
    })


@mcp.tool(
    name="suggest_reconciliation_match",
    description="Suggest the best reconciliation match for a transaction "
                "from a list of candidate ledger entries.",
)
def suggest_reconciliation_match_tool(
    transaction_json: str,
    candidates_json: str,
) -> str:
    """Find best reconciliation match.

    Args:
        transaction_json: JSON string of the transaction to match.
        candidates_json: JSON string of candidate ledger entries.

    Returns:
        JSON string with best match and confidence.
    """
    from providers.finance_ai import suggest_reconciliation_match
    transaction = json.loads(transaction_json)
    candidates = json.loads(candidates_json)
    result = suggest_reconciliation_match(transaction, candidates)
    return json.dumps({
        "success": result.success,
        "data": result.data,
        "confidence": result.confidence,
    })


# ============================================================================
# 9. ANALYTICS TOOLS
# ============================================================================

@mcp.tool(
    name="get_dashboard_summary",
    description="Get dashboard summary metrics: total users, suppliers, "
                "products, orders, and revenue for a given period.",
)
def get_dashboard_summary_tool(
    period: str = "30d",
    country_code: Optional[str] = None,
) -> str:
    """Get dashboard analytics.

    Args:
        period: Time period (7d, 30d, 90d, 1y).
        country_code: Optional ISO country code for filtering.

    Returns:
        JSON string with dashboard metrics.
    """
    from providers.analytics import AnalyticsProvider
    provider = AnalyticsProvider()
    result = provider.get_dashboard_summary(country_code=country_code, period=period)
    return json.dumps(result)


# ============================================================================
# 10. IMAGE TOOLS
# ============================================================================

@mcp.tool(
    name="generate_photo_angles",
    description="Generate descriptions and shooting tips for standard product "
                "photo angles: Front View, Back View, Side View, Detail Shot, In Use.",
)
def generate_photo_angles_tool(
    product_name: str = "",
    category: str = "",
) -> str:
    """Generate product photo angle descriptions.

    Args:
        product_name: Name of the product.
        category: Product category.

    Returns:
        JSON string of angle descriptions with shooting tips.
    """
    from providers.image import generate_angles
    results = generate_angles(b"", product_name=product_name, category=category)
    return json.dumps(results)


# ============================================================================
# SERVER ENTRY POINTS
# ============================================================================

def main():
    """Run the MCP server with stdio transport (default for Claude Desktop)."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    logger.info("Starting Zozi AI Providers MCP server (stdio)...")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
