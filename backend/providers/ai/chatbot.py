from __future__ import annotations

"""
Chatbot Provider
================
AI-powered chatbot with vectorization for product search and customer chat.
Test file: backend/tests/_test_provider/test_chatbot.py
"""
import logging
from typing import Any, Dict, List, Optional


class settings:
    ollama_text_model = "gpt-4o-mini"
    ollama_model = "gpt-4o-mini"
    ollama_base_url = "http://localhost:11434"
    chatbot_vector_model = "nomic-embed-text"
    chatbot_top_k = 10
    chatbot_timeout = 30

logger = logging.getLogger(__name__)


class ChatbotProvider:
    """AI-powered chatbot with vectorization for product search and customer chat."""

    def __init__(self):
        self._session_history: Dict[str, Dict[str, Any]] = {}
        self._session_ttl = settings.chatbot_session_ttl_hours * 3600
        self._max_history = settings.chatbot_max_history

    def process_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Process a chatbot query and return a response.

        Args:
            query: User's message.
            session_id: Optional session identifier.
            user_id: Optional user identifier.

        Returns:
            Dict with response text, intent, and optional product suggestions.
        """
        sid = session_id or "default"
        intent = self._classify_intent(query)
        response_text = self._generate_response(intent, query)

        self._append_to_session(sid, "user", query)
        self._append_to_session(sid, "bot", response_text)

        return {
            "session_id": sid,
            "intent": intent,
            "response": response_text,
            "products": [],
        }

    def _classify_intent(self, query: str) -> str:
        query_lower = query.lower()

        intent_patterns = [
            ("product_search", [
                "find", "show", "search", "looking for", "recommend", "suggest",
                "any", "cheapest", "best", "top", "latest", "new", "cheap",
                "budget", "affordable", "premium", "quality",
            ]),
            ("order_status", ["my order", "order status", "track"]),
            ("shipping", ["ship", "deliver", "dispatch", "arrive", "how long"]),
            ("return", ["return", "refund", "exchange", "broken", "damaged", "wrong"]),
            ("payment", ["pay", "card", "stripe", "tap", "price", "cost", "amount", "checkout"]),
            ("account", ["account", "profile", "password", "login", "sign in", "register"]),
            ("help", ["help", "support", "contact", "assist"]),
            ("greeting", ["hi", "hello", "hey", "salaam", "السلام عليكم"]),
        ]

        for intent, patterns in intent_patterns:
            for pattern in patterns:
                if pattern in query_lower:
                    return intent

        return "general"

    def _generate_response(self, intent: str, query: str) -> str:
        responses = {
            "product_search": "I can help you find products. What are you looking for?",
            "order_status": "Please provide your order number so I can check the status.",
            "shipping": "Shipping typically takes 3-7 business days. Would you like details for your order?",
            "return": "I can help with returns. Please provide your order number and reason for return.",
            "payment": "We accept credit cards, debit cards, and online payment methods.",
            "account": "I can help with account-related questions. What do you need?",
            "help": "I'm here to help! You can ask about products, orders, shipping, returns, or payments.",
            "greeting": "Hello! Welcome to ZOZI. How can I assist you today?",
            "general": "I'm your ZOZI assistant. Ask me about products, orders, or anything else!",
        }
        return responses.get(intent, responses["general"])

    def _append_to_session(self, session_id: str, role: str, text: str) -> None:
        if session_id not in self._session_history:
            self._session_history[session_id] = {"messages": [], "last_active": 0}
        msgs = self._session_history[session_id]["messages"]
        msgs.append({"role": role, "text": text})
        self._session_history[session_id]["messages"] = msgs[-self._max_history:]
        self._session_history[session_id]["last_active"] = __import__("time").monotonic()

    def get_session_history(self, session_id: str) -> List[Dict[str, str]]:
        session = self._session_history.get(session_id, {})
        return session.get("messages", [])

    def clear_session(self, session_id: str) -> None:
        self._session_history.pop(session_id, None)