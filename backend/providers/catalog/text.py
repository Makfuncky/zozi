"""Catalog text provider - re-export from ai.text for backward compatibility."""
from providers.ai.text import embed_text, cosine_similarity, _ollama_chat, _ollama_vision_chat, _extract_json

__all__ = ["embed_text", "cosine_similarity", "_ollama_chat", "_ollama_vision_chat", "_extract_json"]