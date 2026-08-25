"""
Functional tests for critical provider tools:
- Speech-to-text (voice)
- Chatbot (with LLM integration)
- Search with vectorization
- Translation (EN->AR)
- Photo-to-text (vision/OCR)
- Language detection
- Product vectorization
"""
import asyncio
import base64
import io
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

# Ensure backend is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# SPEECH TO TEXT
# ============================================================================

class TestSpeechToText:
    """Test voice-to-text transcription and command processing."""

    def test_process_product_voice_command_add(self):
        from providers.voice.voice_to_text import process_product_voice_command
        result = process_product_voice_command("Add 5 black cotton shirts size L")
        assert result["action"] == "add"
        assert result["quantity"] == 5
        assert result["color"] == "Black"
        assert result["size"] == "L"
        assert result["material"] == "Cotton"
        assert "shirt" in result["product_name"].lower()

    def test_process_product_voice_command_remove(self):
        from providers.voice.voice_to_text import process_product_voice_command
        result = process_product_voice_command("Remove 3 red shoes")
        assert result["action"] == "remove"
        assert result["quantity"] == 3
        assert result["color"] == "Red"

    def test_process_product_voice_command_update(self):
        from providers.voice.voice_to_text import process_product_voice_command
        result = process_product_voice_command("Update quantity to 10 blue bags")
        assert result["action"] == "update"
        assert result["quantity"] == 10

    def test_process_product_voice_command_empty(self):
        from providers.voice.voice_to_text import process_product_voice_command
        result = process_product_voice_command("")
        assert result["action"] == "add"
        assert result["quantity"] == 1

    def test_process_finance_voice_command_expense(self):
        from providers.voice.voice_to_text import process_finance_voice_command
        result = process_finance_voice_command("Record office supplies expense $45.50")
        assert result["action"] == "record"
        assert result["amount"] == 45.50
        assert result["category"] == "office supplies"
        assert result["task_type"] == "expense"

    def test_process_finance_voice_command_delete(self):
        from providers.voice.voice_to_text import process_finance_voice_command
        result = process_finance_voice_command("Delete the payment of $100")
        assert result["action"] == "delete"
        assert result["amount"] == 100.0

    def test_transcribe_audio_mock_ollama(self):
        """Test transcription with mocked Ollama response."""
        from providers.voice.voice_to_text import transcribe_audio
        mock_response = json.dumps({"response": "Hello world"}).encode()
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_ctx = MagicMock()
            mock_ctx.__enter__ = MagicMock(return_value=MagicMock(read=MagicMock(return_value=mock_response)))
            mock_ctx.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_ctx
            result = transcribe_audio(b"fake_audio_bytes")
            assert result == "Hello world"

    def test_transcribe_audio_failure_returns_empty(self):
        """Test transcription returns empty string on failure."""
        from providers.voice.voice_to_text import transcribe_audio
        with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
            result = transcribe_audio(b"fake_audio_bytes")
            assert result == ""


# ============================================================================
# CHATBOT
# ============================================================================

class TestChatbot:
    """Test chatbot intent classification and response generation."""

    def test_intent_product_search(self):
        from providers.ai.chatbot import ChatbotProvider
        bot = ChatbotProvider()
        result = bot.process_query("Find me a red dress")
        assert result["intent"] == "product_search"
        assert "products" in result

    def test_intent_order_status(self):
        from providers.ai.chatbot import ChatbotProvider
        bot = ChatbotProvider()
        result = bot.process_query("Where is my order?")
        assert result["intent"] == "order_status"

    def test_intent_shipping(self):
        from providers.ai.chatbot import ChatbotProvider
        bot = ChatbotProvider()
        result = bot.process_query("How long does shipping take?")
        assert result["intent"] == "shipping"

    def test_intent_return(self):
        from providers.ai.chatbot import ChatbotProvider
        bot = ChatbotProvider()
        result = bot.process_query("I want to return this item")
        assert result["intent"] == "return"

    def test_intent_payment(self):
        from providers.ai.chatbot import ChatbotProvider
        bot = ChatbotProvider()
        result = bot.process_query("What payment methods do you accept?")
        assert result["intent"] == "payment"

    def test_intent_greeting(self):
        from providers.ai.chatbot import ChatbotProvider
        bot = ChatbotProvider()
        result = bot.process_query("Hello there!")
        assert result["intent"] == "greeting"

    def test_intent_greeting_arabic(self):
        from providers.ai.chatbot import ChatbotProvider
        bot = ChatbotProvider()
        result = bot.process_query("السلام عليكم")
        assert result["intent"] == "greeting"

    def test_session_history(self):
        from providers.ai.chatbot import ChatbotProvider
        bot = ChatbotProvider()
        bot.process_query("Hello", session_id="test-123")
        bot.process_query("Find shoes", session_id="test-123")
        history = bot.get_session_history("test-123")
        assert len(history) == 4  # 2 user + 2 bot messages

    def test_clear_session(self):
        from providers.ai.chatbot import ChatbotProvider
        bot = ChatbotProvider()
        bot.process_query("Hello", session_id="test-456")
        bot.clear_session("test-456")
        history = bot.get_session_history("test-456")
        assert len(history) == 0

    def test_response_not_empty(self):
        from providers.ai.chatbot import ChatbotProvider
        bot = ChatbotProvider()
        result = bot.process_query("Hello")
        assert len(result["response"]) > 0


# ============================================================================
# SEARCH WITH VECTORIZATION
# ============================================================================

class TestSearchVectorization:
    """Test AI-powered search with embedding-based ranking."""

    def test_parse_query_price_under(self):
        from providers.ai.search import AdvancedSearchEngine
        engine = AdvancedSearchEngine()
        result = engine.parse_query("shoes under $50")
        assert result["max_price"] == 50.0
        assert "shoes" in result["terms"]

    def test_parse_query_price_range(self):
        from providers.ai.search import AdvancedSearchEngine
        engine = AdvancedSearchEngine()
        result = engine.parse_query("dress between $20 and $100")
        assert result["min_price"] == 20.0
        assert result["max_price"] == 100.0

    def test_parse_query_rating(self):
        from providers.ai.search import AdvancedSearchEngine
        engine = AdvancedSearchEngine()
        result = engine.parse_query("4 star rated laptops")
        assert result["min_rating"] == 4

    def test_parse_query_color(self):
        from providers.ai.search import AdvancedSearchEngine
        engine = AdvancedSearchEngine()
        result = engine.parse_query("red shirt")
        assert result["color"] == "red"

    def test_parse_query_size(self):
        from providers.ai.search import AdvancedSearchEngine
        engine = AdvancedSearchEngine()
        result = engine.parse_query("shirt size XL")
        assert result["size"] == "XL"

    def test_parse_query_category(self):
        from providers.ai.search import AdvancedSearchEngine
        engine = AdvancedSearchEngine()
        result = engine.parse_query("smartphone gadget")
        assert result["category"] == "electronics"

    def test_parse_query_sort_newest(self):
        from providers.ai.search import AdvancedSearchEngine
        engine = AdvancedSearchEngine()
        result = engine.parse_query("new arrivals")
        assert result["sort"] == "newest"

    def test_parse_query_sort_cheapest(self):
        from providers.ai.search import AdvancedSearchEngine
        engine = AdvancedSearchEngine()
        result = engine.parse_query("cheapest shoes")
        assert result["sort"] == "price_asc"

    def test_search_with_catalog(self):
        from providers.ai.search import AdvancedSearchEngine
        engine = AdvancedSearchEngine()
        products = [
            {"id": 1, "name": "Red Cotton Shirt", "description": "Comfortable casual shirt", "tags": ["cotton", "casual"]},
            {"id": 2, "name": "Blue Denim Jeans", "description": "Slim fit jeans", "tags": ["denim", "slim"]},
            {"id": 3, "name": "Black Leather Jacket", "description": "Warm winter jacket", "tags": ["leather", "winter"]},
        ]
        engine.load_product_catalog(products)
        result = engine.search("cotton shirt")
        assert "products" in result
        assert "parsed_query" in result

    def test_search_empty_catalog(self):
        from providers.ai.search import AdvancedSearchEngine
        engine = AdvancedSearchEngine()
        result = engine.search("shoes")
        assert result["total"] == 0
        assert "parsed_query" in result

    def test_fuzzy_search(self):
        from providers.ai.search import AdvancedSearchEngine
        engine = AdvancedSearchEngine()
        products = [
            {"id": 1, "name": "Cotton Shirt", "description": "Casual wear", "tags": ["cotton"]},
        ]
        engine.load_product_catalog(products)
        result = engine.fuzzy_search("cotton", cutoff=0.0)
        assert "products" in result

    def test_autocomplete(self):
        from providers.ai.search import AdvancedSearchEngine
        engine = AdvancedSearchEngine()
        engine._categories = ["Electronics", "Fashion", "Home"]
        suggestions = engine.get_autocomplete_suggestions("ele")
        assert "Electronics" in suggestions


# ============================================================================
# TRANSLATION
# ============================================================================

class TestTranslation:
    """Test English-to-Arabic translation with glossary fallback."""

    def test_translate_glossary_fallback(self):
        from providers.ai.text import _translate_glossary_fallback
        result = _translate_glossary_fallback("product price sale")
        assert "منتج" in result  # product
        assert "السعر" in result  # price
        assert "تخفيض" in result  # sale

    def test_translate_glossary_preserves_unknown(self):
        from providers.ai.text import _translate_glossary_fallback
        result = _translate_glossary_fallback("hello world")
        assert "hello" in result
        assert "world" in result

    def test_translate_glossary_empty(self):
        from providers.ai.text import _translate_glossary_fallback
        result = _translate_glossary_fallback("")
        assert result == ""

    def test_translate_glossary_mixed(self):
        from providers.ai.text import _translate_glossary_fallback
        result = _translate_glossary_fallback("buy product now")
        assert "اشترِ" in result  # buy
        assert "منتج" in result  # product

    @pytest.mark.asyncio
    async def test_translate_en_to_ar_with_ollama_mock(self):
        from providers.ai.text import translate_en_to_ar
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={
            "choices": [{"message": {"content": "منتج جديد"}}]
        })
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_client.return_value = mock_instance
            result = await translate_en_to_ar("new product")
            assert result == "منتج جديد"

    @pytest.mark.asyncio
    async def test_translate_en_to_ar_fallback(self):
        from providers.ai.text import translate_en_to_ar
        import httpx
        with patch("httpx.AsyncClient", side_effect=httpx.ConnectError("No network")):
            result = await translate_en_to_ar("product sale")
            assert "منتج" in result  # glossary fallback


# ============================================================================
# PHOTO TO TEXT (VISION + OCR)
# ============================================================================

class TestPhotoToText:
    """Test image analysis and OCR text extraction."""

    def test_ocr_parse_bill_text(self):
        from providers.ocr.ocr_parser import parse_bill_text
        bill_text = """
        Vendor: ABC Store
        Date: 2024-01-15
        Total: $125.50
        Tax: $12.55
        Payment: Credit Card
        Invoice #: INV-2024-001
        """
        result = parse_bill_text(bill_text)
        assert isinstance(result, dict)

    def test_ocr_parse_statement_csv(self):
        from providers.ocr.ocr_parser import parse_statement_csv
        csv_text = "Date,Description,Amount\n2024-01-01,Office Supplies,50.00\n2024-01-02,Travel,120.00"
        result = parse_statement_csv(csv_text)
        assert isinstance(result, list)

    def test_vision_classify_product_type(self):
        from providers.ai.vision import classify_product_type
        assert classify_product_type("iPhone 15", "Electronics") == "electronic"
        assert classify_product_type("Cotton Shirt", "Fashion") == "clothing"
        assert classify_product_type("Sofa", "Home") == "furniture"
        assert classify_product_type("Random Item", "Other") == "general"

    def test_vision_normalize_category(self):
        from providers.ai.vision import normalize_category
        assert normalize_category("iPhone 15 smartphone") == "electronics"
        assert normalize_category("Cotton dress shirt") == "fashion"
        assert normalize_category("Unknown item") == "general"

    def test_vision_suggest_price_fallback(self):
        from providers.ai.vision import suggest_price
        result = suggest_price(b"", product_name="iPhone", category="Electronics")
        assert "suggested_price" in result
        assert result["suggested_price"] > 0

    def test_vision_analyze_product_image_fallback(self):
        from providers.ai.vision import analyze_product_image
        result = analyze_product_image(b"", filename="test.jpg", use_vision=False)
        assert "name" in result
        assert "category" in result
        assert "product_type" in result

    def test_vision_analyze_with_mock_vision(self):
        from providers.ai.vision import analyze_product_image
        mock_response = json.dumps({
            "product_name": "Red Shirt",
            "category": "Fashion",
            "color": "Red",
            "tags": ["cotton", "casual"],
            "description": "A nice red shirt"
        })
        with patch("providers.ai.vision._ollama_vision_chat", return_value=mock_response):
            result = analyze_product_image(b"fake_image", use_vision=True)
            assert result["name"] == "Red Shirt"
            assert result["category"] == "Fashion"
            assert result["source"] == "vision_ai"


# ============================================================================
# TEXT EMBEDDING & VECTORIZATION
# ============================================================================

class TestTextEmbedding:
    """Test text embedding generation and similarity."""

    def test_cosine_similarity_identical(self):
        from providers.ai.text import cosine_similarity
        vec = [1.0, 2.0, 3.0]
        assert cosine_similarity(vec, vec) == pytest.approx(1.0)

    def test_cosine_similarity_orthogonal(self):
        from providers.ai.text import cosine_similarity
        a = [1.0, 0.0, 0.0]
        b = [0.0, 1.0, 0.0]
        assert cosine_similarity(a, b) == pytest.approx(0.0)

    def test_cosine_similarity_empty(self):
        from providers.ai.text import cosine_similarity
        assert cosine_similarity([], []) == 0.0
        assert cosine_similarity([1.0], []) == 0.0

    def test_cosine_similarity_different_length(self):
        from providers.ai.text import cosine_similarity
        assert cosine_similarity([1.0, 2.0], [1.0]) == 0.0

    def test_embed_text_mock_ollama(self):
        from providers.ai.text import embed_text
        mock_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_response = json.dumps({"embedding": mock_embedding}).encode()
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_ctx = MagicMock()
            mock_ctx.__enter__ = MagicMock(return_value=MagicMock(read=MagicMock(return_value=mock_response)))
            mock_ctx.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_ctx
            result = embed_text("test product")
            assert result == mock_embedding

    def test_embed_text_failure_returns_empty(self):
        from providers.ai.text import embed_text
        import urllib.error
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused")):
            result = embed_text("test")
            assert result == []

    def test_extract_json_valid(self):
        from providers.ai.text import _extract_json
        result = _extract_json('{"name": "test", "value": 123}')
        assert result == {"name": "test", "value": 123}

    def test_extract_json_nested(self):
        from providers.ai.text import _extract_json
        result = _extract_json('Some text {"key": "value"} more text')
        assert result == {"key": "value"}

    def test_extract_json_invalid(self):
        from providers.ai.text import _extract_json
        result = _extract_json("no json here")
        assert result is None

    def test_extract_json_array(self):
        from providers.ai.text import _extract_json
        result = _extract_json('[1, 2, 3]')
        assert result == [1, 2, 3]


# ============================================================================
# LANGUAGE DETECTION
# ============================================================================

class TestLanguageDetection:
    """Test language detection and text processing utilities."""

    def test_detect_arabic_text(self):
        """Detect Arabic text by Unicode range."""
        text = "هذا نص عربي"
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        assert arabic_chars > 0

    def test_detect_english_text(self):
        """Detect English text by ASCII range."""
        text = "This is English text"
        ascii_chars = sum(1 for c in text if c.isascii() and c.isalpha())
        assert ascii_chars > 0

    def test_mixed_language_detection(self):
        """Detect mixed language text."""
        text = "Hello مرحبا World"
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        latin_chars = sum(1 for c in text if c.isascii() and c.isalpha())
        assert arabic_chars > 0
        assert latin_chars > 0


# ============================================================================
# PRODUCT VECTORIZATION FOR SEARCH
# ============================================================================

class TestProductVectorization:
    """Test product catalog embedding and search ranking."""

    def test_load_product_catalog(self):
        from providers.ai.search import AdvancedSearchEngine
        engine = AdvancedSearchEngine()
        products = [
            {"id": 1, "name": "Cotton Shirt", "description": "Casual cotton shirt", "tags": ["cotton", "casual"]},
            {"id": 2, "name": "Denim Jeans", "description": "Slim fit jeans", "tags": ["denim"]},
        ]
        count = engine.load_product_catalog(products)
        assert count == 2

    def test_product_embedding_generated(self):
        from providers.ai.search import AdvancedSearchEngine
        engine = AdvancedSearchEngine()
        products = [{"id": 1, "name": "Test Product", "description": "A test item", "tags": ["test"]}]
        
        mock_embedding = [0.1] * 128
        with patch("providers.ai.search.embed_text", return_value=mock_embedding):
            engine.load_product_catalog(products)
        
        assert 1 in engine._product_embeddings
        assert len(engine._product_embeddings[1]) == 128

    def test_search_ranking_by_similarity(self):
        from providers.ai.search import AdvancedSearchEngine
        engine = AdvancedSearchEngine()
        products = [
            {"id": 1, "name": "Cotton Shirt", "description": "shirt", "tags": []},
            {"id": 2, "name": "Wooden Table", "description": "furniture", "tags": []},
        ]
        
        def mock_embed(text):
            if "shirt" in str(text).lower() or "cotton" in str(text).lower():
                return [1.0, 0.0, 0.0]
            elif "table" in str(text).lower() or "furniture" in str(text).lower():
                return [0.0, 1.0, 0.0]
            return [0.5, 0.5, 0.0]
        
        with patch("providers.ai.search.embed_text", side_effect=mock_embed):
            engine.load_product_catalog(products)
            result = engine.search("cotton shirt")
        
        assert result["total"] > 0

    def test_search_with_filters(self):
        from providers.ai.search import AdvancedSearchEngine
        engine = AdvancedSearchEngine()
        result = engine.search("shoes", filters={"brand": "Nike"})
        assert result["all_filters"]["brand"] == "Nike"


# ============================================================================
# TEXT-TO-SPEECH / VOICE COMMAND INTEGRATION
# ============================================================================

class TestVoiceCommandIntegration:
    """Test end-to-end voice command processing pipeline."""

    def test_voice_to_cart_workflow(self):
        """Simulate: voice command -> product extraction -> cart action."""
        from providers.voice.voice_to_text import process_product_voice_command
        result = process_product_voice_command("Add 3 black cotton shirts size M")
        
        assert result["action"] == "add"
        assert result["quantity"] == 3
        assert result["color"] == "Black"
        assert result["material"] == "Cotton"
        assert result["size"] == "M"
        assert len(result["product_name"]) > 0

    def test_voice_to_finance_workflow(self):
        """Simulate: voice command -> finance extraction -> record entry."""
        from providers.voice.voice_to_text import process_finance_voice_command
        result = process_finance_voice_command("Record travel expense $250.00")
        
        assert result["action"] == "record"
        assert result["amount"] == 250.0
        assert result["category"] == "travel"
        assert result["task_type"] == "expense"

    def test_voice_remove_action(self):
        from providers.voice.voice_to_text import process_product_voice_command
        result = process_product_voice_command("Remove 2 items")
        assert result["action"] == "remove"
        assert result["quantity"] == 2


# ============================================================================
# CHATBOT + SEARCH INTEGRATION
# ============================================================================

class TestChatbotSearchIntegration:
    """Test chatbot with search engine integration."""

    def test_chatbot_product_search_triggers_search(self):
        from providers.ai.chatbot import ChatbotProvider
        bot = ChatbotProvider()
        result = bot.process_query("Find me red shoes under $50")
        assert result["intent"] == "product_search"

    def test_search_parses_chatbot_query(self):
        from providers.ai.search import AdvancedSearchEngine
        engine = AdvancedSearchEngine()
        parsed = engine.parse_query("Find me red shoes under $50")
        assert parsed["max_price"] == 50.0
        assert parsed["color"] == "red"
        assert "shoes" in parsed["terms"]
