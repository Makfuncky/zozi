"""Diagnostic: probe which BiRefNet rembg sessions are loadable.

Import-safe: model loading only runs when executed directly
(``python -m providers.legacy.check_BiRefNet``), not on package import.
"""
from __future__ import annotations


def check_birefnet() -> None:
    from rembg import new_session

    model_names = [
        "birefnet-general",
        "birefnet-general-lite",
        "birefnet-portrait",
        "birefnet-massive",
        "birefnet-dis",
        "birefnet-hrsod",
        "birefnet-cod",
        "birefnet-mo",
    ]

    available = []
    for model_name in model_names:
        try:
            new_session(model_name)
            available.append(model_name)
            print(f"[OK] {model_name} - AVAILABLE")
        except Exception as exc:  # noqa: BLE001
            print(f"[NO] {model_name} - Not available: {exc}")

    if not available:
        try:
            from rembg.sessions import sessions_class

            print(f"Available models: {list(sessions_class.keys())}")
        except Exception as exc:  # noqa: BLE001
            print(f"Could not list available models: {exc}")


if __name__ == "__main__":
    check_birefnet()
