#!/usr/bin/env python3
"""
ZOZI Enterprise Product Upload Engine - AUTOMATIC EDITION
=====================================================
✅ Fully automatic (no manual input) — bulk uploads a folder of images
✅ Connected to the live ZOZI Supplier Upload API (/supplier/upload)
✅ AI product detection via local Ollama (moondream vision + phi3:mini text)
✅ Graceful fallback to the backend AI analyzer when Ollama is offline
✅ Auto-generated price / stock / variants from detected product data
✅ Free image-enhancement pipeline enabled on every upload (webp/compress/etc.)
✅ Optional "clean" mode deletes the supplier's existing products first

Usage:
    python upload_auto_05.py                      # auto: processes ../image, cleans first
    python upload_auto_05.py --no-clean           # keep existing products
    python upload_auto_05.py --folder D:/images   # custom image folder
    python upload_auto_05.py --email x@y.com --password secret
    python upload_auto_05.py --limit 5            # process only first N images
"""

import os
import sys
import json
import csv
import uuid
import re
import base64
import argparse
import itertools
import time
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import httpx
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION LOADER
# ============================================================================

class ConfigLoader:
    """Loads configuration from JSON file"""

    def __init__(self, config_file: str = "zozi_variant_config.json"):
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info(f"✅ Loaded configuration from {self.config_file}")
                logger.info(f"   - Variants: {len(config.get('variants', {}))}")
                logger.info(f"   - Product Types: {len(config.get('product_type_keywords', {}))}")
                return config
        except FileNotFoundError:
            logger.error(f"❌ Configuration file not found: {self.config_file}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in {self.config_file}: {e}")
            raise

    def get_variants(self) -> Dict[str, Any]:
        return self.config.get("variants", {})

    def get_product_type_keywords(self) -> Dict[str, List[str]]:
        keywords = self.config.get("product_type_keywords", {})
        if "clothing" in keywords:
            additional = ["lingerie", "bralette", "bra", "underwear", "panties"]
            for item in additional:
                if item not in keywords["clothing"]:
                    keywords["clothing"].append(item)
        return keywords

    def get_category_fallbacks(self) -> Dict[str, List[str]]:
        return self.config.get("category_fallbacks", {})

    def get_ai_rules(self) -> Dict[str, Any]:
        return self.config.get("ai_rules", {})

    def get_variant_info(self, variant_key: str) -> Dict[str, Any]:
        return self.get_variants().get(variant_key, {})

    def get_mutually_exclusive(self, variant_key: str) -> List[str]:
        variant_info = self.get_variant_info(variant_key)
        return variant_info.get("mutually_exclusive_with", [])


# ============================================================================
# MASTER ATTRIBUTE DATABASE (JSON-Driven)
# ============================================================================

class MasterAttributeDatabase:
    """JSON-driven master database of all e-commerce variants"""

    def __init__(self, config_loader: ConfigLoader):
        self.config = config_loader

    def classify_product_type(self, product_name: str, category: str, subcategory: str) -> str:
        text = f"{product_name} {category} {subcategory}".lower()
        keywords = self.config.get_product_type_keywords()

        for product_type, type_keywords in keywords.items():
            if any(kw in text for kw in type_keywords):
                return product_type

        category_lower = category.lower()
        fallbacks = self.config.get_category_fallbacks()

        if any(kw in category_lower for kw in fallbacks.get("apparel_keywords", [])):
            return "clothing"
        elif any(kw in category_lower for kw in fallbacks.get("electronics_keywords", [])):
            return "electronic"
        elif any(kw in category_lower for kw in fallbacks.get("furniture_keywords", [])):
            return "furniture"
        elif any(kw in category_lower for kw in fallbacks.get("home_keywords", [])):
            return "appliance"
        elif any(kw in category_lower for kw in fallbacks.get("jewelry_keywords", [])):
            return "jewelry"
        elif any(kw in category_lower for kw in fallbacks.get("beauty_keywords", [])):
            return "beauty"
        elif any(kw in category_lower for kw in fallbacks.get("groceries_keywords", [])):
            return "food_solid"
        elif any(kw in category_lower for kw in fallbacks.get("toys_keywords", [])):
            return "toy"
        elif any(kw in category_lower for kw in fallbacks.get("books_keywords", [])):
            return "book"
        elif any(kw in category_lower for kw in fallbacks.get("automotive_keywords", [])):
            return "automotive"

        return "general"

    def get_allowed_variants(self, category: str, subcategory: str) -> List[str]:
        category_lower = category.lower().strip()
        subcategory_lower = subcategory.lower().strip()
        variants = self.config.get_variants()

        allowed = []

        for variant_key, variant_data in variants.items():
            if category_lower in variant_data.get("categories", []) or \
               subcategory_lower in variant_data.get("categories", []):
                allowed.append(variant_key)

        if not allowed:
            for variant_key, variant_data in variants.items():
                for cat in variant_data.get("categories", []):
                    if category_lower in cat or cat in category_lower or \
                       subcategory_lower in cat or cat in subcategory_lower:
                        if variant_key not in allowed:
                            allowed.append(variant_key)

        if not allowed:
            fallbacks = self.config.get_category_fallbacks()
            if any(kw in category_lower or kw in subcategory_lower for kw in fallbacks.get("apparel_keywords", [])):
                allowed = ["color", "size", "material", "pattern", "gender"]
            elif any(kw in category_lower or kw in subcategory_lower for kw in fallbacks.get("electronics_keywords", [])):
                allowed = ["color", "storage", "ram", "model", "screen_size"]
            elif any(kw in category_lower or kw in subcategory_lower for kw in fallbacks.get("jewelry_keywords", [])):
                allowed = ["color", "material", "plating", "size"]
            elif any(kw in category_lower or kw in subcategory_lower for kw in fallbacks.get("home_keywords", [])):
                allowed = ["color", "material", "dimensions", "capacity"]
            elif any(kw in category_lower or kw in subcategory_lower for kw in fallbacks.get("beauty_keywords", [])):
                allowed = ["color", "volume", "weight", "scent", "skin_type"]
            elif any(kw in category_lower or kw in subcategory_lower for kw in fallbacks.get("groceries_keywords", [])):
                allowed = ["flavor", "weight", "volume"]
            elif any(kw in category_lower or kw in subcategory_lower for kw in fallbacks.get("toys_keywords", [])):
                allowed = ["color", "size", "age_group"]
            elif any(kw in category_lower or kw in subcategory_lower for kw in fallbacks.get("automotive_keywords", [])):
                allowed = ["color", "car_fitment", "vehicle_type", "year"]

        if not allowed:
            allowed = ["color"]

        return allowed

    def extract_variant_options(self, variant_key: str) -> List[str]:
        info = self.get_variant_info(variant_key)
        opts = info.get("options") or info.get("values") or []
        if isinstance(opts, list):
            cleaned = [str(o).strip() for o in opts if str(o).strip()]
            return cleaned[:12]
        return []

    def get_variant_info(self, variant_key: str) -> Dict[str, Any]:
        return self.config.get_variant_info(variant_key)

    def get_mutually_exclusive(self, variant_key: str) -> List[str]:
        return self.config.get_mutually_exclusive(variant_key)


# ============================================================================
# SYSTEM CONFIGURATION
# ============================================================================

@dataclass
class SystemConfig:
    """System configuration for the automatic upload engine."""

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "phi3:mini"
    OLLAMA_VISION_MODEL: str = "moondream"

    OLLAMA_MAX_RETRIES: int = 2
    OLLAMA_RETRY_DELAY: float = 3.0
    OLLAMA_TIMEOUT: float = 600.0

    BACKEND_URL: str = "http://localhost:8000"
    SUPPLIER_EMAIL: str = "supplier@zozi.com"
    SUPPLIER_PASSWORD: str = "supplier123"

    OUTPUT_DIR: str = "products_output"

    IMAGE_TOOLS: Dict[str, bool] = None

    # Concurrent upload settings
    CONCURRENCY: int = 3  # number of parallel uploads (phase 2 only)
    USE_OLLAMA: bool = True  # use Ollama for proper AI vision detection

    def __post_init__(self):
        if self.IMAGE_TOOLS is None:
            self.IMAGE_TOOLS = {
                "magic_erase": False,    # bg removal — off by default (keeps original bg)
                "smart_crop": True,
                "rotate": False,
                "auto_light": True,
                "upscale": False,
                "white_balance": True,
                "denoise": True,
                "sharpen": True,
                "compress": True,
                "webp_convert": True,
                "color_enhance": True,
                "auto_levels": True,
            }

    @classmethod
    async def validate(cls):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{cls.BACKEND_URL}/health")
                if r.status_code == 200:
                    logger.info(f"✅ Backend reachable: {cls.BACKEND_URL}")
                else:
                    logger.warning(f"⚠️  Backend returned {r.status_code}")
        except Exception as e:
            logger.warning(f"⚠️  Backend not reachable ({e}). Uploads will fail.")


# ============================================================================
# IMAGE HELPERS
# ============================================================================

def to_jpeg_bytes(image_path: str) -> bytes:
    """Returnimage bytes as JPEG (RGB). Falls back to original bytes if PIL missing."""
    try:
        from io import BytesIO
        from PIL import Image
        img = Image.open(image_path).convert("RGB")
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=92)
        return buf.getvalue()
    except Exception:
        with open(image_path, "rb") as f:
            return f.read()


# ============================================================================
# BACKEND CLIENT  (ZOZI Supplier Upload API)
# ============================================================================

class BackendClient:
    """Talks to the live ZOZI supplier API: auth, AI analyze, upload, clean."""

    MIME = {
        "webp": "image/webp", "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "png": "image/png", "gif": "image/gif"
    }

    def __init__(self, config: SystemConfig):
        self.config = config
        self.token: Optional[str] = None
        self.client = httpx.AsyncClient(
            base_url=config.BACKEND_URL,
            timeout=120.0,
            limits=httpx.Limits(max_connections=4, max_keepalive_connections=2)
        )

    @property
    def _auth(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    def _mime(self, image_path: str) -> str:
        ext = Path(image_path).suffix.lower().lstrip(".")
        return self.MIME.get(ext, "image/jpeg")

    async def login(self) -> str:
        r = await self.client.post(
            "/auth/login",
            data={"username": self.config.SUPPLIER_EMAIL,
                  "password": self.config.SUPPLIER_PASSWORD}
        )
        if r.status_code != 200:
            raise ConnectionError(f"Login failed ({r.status_code}): {r.text[:200]}")
        self.token = r.json()["access_token"]
        logger.info(f"🔑 Logged in as {self.config.SUPPLIER_EMAIL}")
        return self.token

    async def ai_analyze(self, image_path: str) -> Dict[str, Any]:
        """Backend AI analyzer (uses moondream internally — send JPEG so vision works)."""
        data = to_jpeg_bytes(image_path)
        r = await self.client.post(
            "/supplier/upload/ai-analyze",
            headers=self._auth,
            files={"image": (Path(image_path).stem + ".jpg", data, "image/jpeg")}
        )
        if r.status_code != 200:
            logger.warning(f"⚠️  ai-analyze failed ({r.status_code}): {r.text[:120]}")
            return {}
        return r.json()

    async def list_products(self, limit: int = 200) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        offset = 0
        while True:
            r = await self.client.get(
                f"/supplier/products?limit={limit}&offset={offset}", headers=self._auth)
            if r.status_code != 200:
                logger.warning(f"⚠️  list products failed ({r.status_code})")
                break
            payload = r.json()
            batch = payload.get("data") or []
            out.extend(batch)
            total = payload.get("total", 0)
            if not batch or len(out) >= total:
                break
            offset += limit
        return out

    async def delete_product(self, product_id: int) -> bool:
        r = await self.client.delete(f"/supplier/products/{product_id}", headers=self._auth)
        return r.status_code in (200, 204)

    async def clean_all_products(self) -> int:
        products = await self.list_products()
        deleted = 0
        for p in products:
            pid = p.get("id")
            if pid is None:
                continue
            if await self.delete_product(pid):
                deleted += 1
                logger.info(f"🗑️  Deleted product #{pid} ({p.get('name', '?')})")
        logger.info(f"🧹 Cleaned {deleted} existing product(s)")
        return deleted

    async def upload_product(self, image_path: str, fields: Dict[str, Any],
                             tool_flags: Dict[str, bool]) -> Dict[str, Any]:
        data = open(image_path, "rb").read()
        form: Dict[str, Any] = {}
        for k, v in fields.items():
            if v is None or v == "":
                continue
            form[k] = v
        for k, v in tool_flags.items():
            form[k] = "true" if v else "false"
        r = await self.client.post(
            "/supplier/upload",
            headers=self._auth,
            data=form,
            files={"image": (Path(image_path).name, data, self._mime(image_path))}
        )
        try:
            j = r.json()
        except Exception:
            j = None
        return {"status": r.status_code, "body": r.text, "json": j}

    async def close(self):
        await self.client.aclose()


# ============================================================================
# AI SERVICES (Ollama — native /api/chat, used only when available)
# ============================================================================

class AIService:
    """Ollama-based AI (moondream vision + phi3:mini text) via native /api/chat."""

    def __init__(self, config: SystemConfig, master_db: MasterAttributeDatabase):
        self.config = config
        self.master_db = master_db
        self.available = False
        self._check_availability()
        self.client = httpx.AsyncClient(
            base_url=config.OLLAMA_BASE_URL,
            timeout=config.OLLAMA_TIMEOUT,
            limits=httpx.Limits(max_connections=4, max_keepalive_connections=2)
        )
        self.performance_metrics = {'vision_calls': 0, 'text_calls': 0, 'total_time': 0.0}

    def _check_availability(self):
        if not self.config.USE_OLLAMA:
            self.available = False
            logger.info("🤖 Ollama disabled (--ollama flag not set) — using fast backend AI analyzer")
            return
        try:
            r = httpx.get(f"{self.config.OLLAMA_BASE_URL}/api/tags", timeout=3.0)
            if r.status_code == 200:
                self.available = True
                logger.info("🤖 Ollama detected — using local AI vision + text")
            else:
                logger.info("🤖 Ollama not ready — using backend AI analyzer fallback")
        except Exception:
            logger.info("🤖 Ollama unreachable — using backend AI analyzer fallback")

    async def _ollama_chat(self, model: str, content: str, images: Optional[List[str]] = None,
                           num_predict: int = 400, temperature: float = 0.2) -> str:
        if not self.available:
            raise RuntimeError("Ollama unavailable")
        msg: Dict[str, Any] = {"role": "user", "content": content}
        if images:
            msg["images"] = images
        payload = {
            "model": model,
            "messages": [msg],
            "stream": False,
            "options": {"num_predict": num_predict, "temperature": temperature, "keep_alive": "10m"}
        }
        last = None
        for _ in range(self.config.OLLAMA_MAX_RETRIES):
            try:
                start = time.time()
                resp = await self.client.post("/api/chat", json=payload)
                elapsed = time.time() - start
                resp.raise_for_status()
                text = resp.json()["message"]["content"]
                self.performance_metrics['total_time'] += elapsed
                return text
            except Exception as e:
                last = e
                logger.warning(f"⚠️  Ollama {model} call failed: {e}")
                await asyncio.sleep(self.config.OLLAMA_RETRY_DELAY)
        raise last or RuntimeError("Ollama call failed")

    def _extract_json(self, content: str) -> Dict[str, Any]:
        content = content.strip()
        if "```" in content:
            content = re.sub(r'```[a-zA-Z]*\n?', '', content)
            content = re.sub(r'\n?```$', '', content)
        m = re.search(r'\{[\s\S]*\}', content)
        if not m:
            raise ValueError("No JSON found")
        raw = m.group()
        # Attempt normal parse first
        try:
            return json.loads(raw, strict=False)
        except json.JSONDecodeError:
            pass
        # Fix common phi3:mini JSON issues:
        s = raw
        # Escape unescaped single quotes inside strings (except for apostrophes)
        s = re.sub(r"(?<!\\)'", '"', s)
        # Fix Python None/null
        s = re.sub(r'\bNone\b', 'null', s)
        s = re.sub(r'\bTrue\b', 'true', s)
        s = re.sub(r'\bFalse\b', 'false', s)
        # Remove trailing commas before } or ]
        s = re.sub(r',\s*}', '}', s)
        s = re.sub(r',\s*]', ']', s)
        # Remove comments
        s = re.sub(r'//[^\n]*', '', s)
        try:
            return json.loads(s, strict=False)
        except json.JSONDecodeError:
            pass
        # Try to extract key-value pairs using regex as last resort
        kv = re.findall(r'"([^"]+)"\s*:\s*"([^"]*)"', s)
        if kv:
            return dict(kv)
        kv2 = re.findall(r"'([^']+)'\s*:\s*'([^']*)'", s)
        if kv2:
            return dict(kv2)
        raise ValueError(f"Could not parse JSON from phi3:mini output: {raw[:200]}")

    async def analyze_and_describe(self, image_path: str, allowed: List[str]) -> Dict[str, Any]:
        """One vision call + one text call → full structured analysis + EN/AR descriptions."""
        if not self.available:
            return {}
        logger.info(f"🔍 Analyzing image: {os.path.basename(image_path)}")
        jpg = to_jpeg_bytes(image_path)
        b64 = base64.b64encode(jpg).decode("utf-8")

        vision_prompt = (
            "Look at this product photo. In 2-4 short factual sentences describe exactly what "
            "the product is: its name, brand if visible, category, type, color(s), material, and "
            "condition (new/used). Do not invent details you cannot see."
        )
        raw = await self._ollama_chat(
            self.config.OLLAMA_VISION_MODEL, vision_prompt,
            images=[b64], num_predict=200, temperature=0.2)
        logger.info(f"👁️ Vision: {raw.strip()[:140]}")
        self.performance_metrics['vision_calls'] += 1

        # Extract product name from vision description as fallback
        vision_words = raw.strip().split()
        vision_name = " ".join(vision_words[:6]).strip(".,;:!?").title() if vision_words else "Product"
        # Remove leading "The " or "A " or "An "
        vision_name = re.sub(r'^(The|A|An)\s+', '', vision_name, flags=re.IGNORECASE)

        combined_prompt = f"""You are a product data specialist. Based on the image description below, produce a JSON object.

IMAGE DESCRIPTION:
{raw}

ALLOWED VARIANT KEYS (only choose from this list): {json.dumps(allowed)}

RULES:
- Choose category from: Electronics, Fashion, Home, Beauty, Jewelry, Automotive, Toys, Groceries, Sports, Books, Apparel, Lingerie, Furniture, Appliances
- If liquids use "volume" not "weight"; if solid food use "weight" not "volume"; if clothing use "size".
- Return ONLY valid JSON, no explanations. Use double quotes for all keys and string values.

JSON FIELDS:
{{
  "product_name": str,
  "category": str,
  "subcategory": str,
  "detected_attributes": {{"color": str or null, "material": str or null, "brand": str or null}},
  "relevant_variants": [list of keys from ALLOWED VARIANT KEYS],
  "english_title": str (60-80 chars, SEO),
  "english_description": str (3 sentences + bullet points with ✅),
  "arabic_title": str,
  "arabic_description": str (وصف احترافي مع نقاط ✅),
  "bullet_points_en": [3-5 strings],
  "bullet_points_ar": [3-5 strings]
}}

OUTPUT:"""
        text = await self._ollama_chat(
            self.config.OLLAMA_MODEL, combined_prompt,
            num_predict=800, temperature=0.3)
        self.performance_metrics['text_calls'] += 1

        try:
            result = self._extract_json(text)
        except Exception as e:
            logger.warning(f"⚠️ JSON parsing from phi3:mini failed ({e}), using vision-derived name")
            # Return partial result based on vision description
            words = raw.strip().split()
            detected_color = next((w.lower() for w in words if w.lower() in
                                   ['black','white','red','blue','green','yellow','orange',
                                    'purple','pink','brown','grey','gray','silver','gold']), None)
            return {
                "product_name": vision_name,
                "category": "General",
                "subcategory": "General",
                "detected_attributes": {"color": detected_color} if detected_color else {},
                "relevant_variants": ["color"],
                "variant_options": {},
                "product_type": "general",
                "condition": "new",
                "descriptions": {},
                "source": "ollama_partial",
            }

        # normalize
        detected = {k: v for k, v in (result.get("detected_attributes") or {}).items()
                    if v and v not in [None, "", "null", "N/A", "n/a"]}
        relevant = [v for v in (result.get("relevant_variants") or []) if v in allowed]
        relevant = self._apply_mutual_exclusion(relevant)
        category = result.get("category") or "General"
        subcategory = result.get("subcategory") or "General"
        product_type = self.master_db.classify_product_type(
            result.get("product_name", ""), category, subcategory)
        return {
            "product_name": result.get("product_name") or vision_name,
            "category": category,
            "subcategory": subcategory,
            "detected_attributes": detected,
            "relevant_variants": relevant,
            "variant_options": detected,
            "product_type": product_type,
            "condition": "new",
            "descriptions": {
                "english_title": result.get("english_title", ""),
                "english_description": result.get("english_description", ""),
                "arabic_title": result.get("arabic_title", ""),
                "arabic_description": result.get("arabic_description", ""),
                "bullet_points_en": result.get("bullet_points_en") or [],
                "bullet_points_ar": result.get("bullet_points_ar") or [],
            },
            "source": "ollama",
        }

    def _apply_mutual_exclusion(self, variants):
        result = variants.copy()
        for variant in variants:
            if variant in result:
                for ex in self.master_db.get_mutually_exclusive(variant):
                    if ex in result:
                        result.remove(ex)
        return result

    async def close(self):
        await self.client.aclose()


# ============================================================================
# CSV EXPORT (traceability backup)
# ============================================================================

class CSVExporter:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.filepath = self.output_dir / "zozi_products_uploaded.csv"
        self.fieldnames = [
            'product_id', 'sku', 'timestamp', 'product_name', 'category', 'subcategory',
            'price_omr', 'stock_quantity', 'condition', 'english_title', 'english_description',
            'arabic_title', 'attributes', 'image_path', 'backend_status', 'backend_id'
        ]

    def save(self, row: Dict[str, Any]):
        file_exists = self.filepath.exists()
        with open(self.filepath, 'a', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=self.fieldnames)
            if not file_exists:
                w.writeheader()
            w.writerow(row)
        logger.info(f"✅ Logged to CSV: {self.filepath}")


# ============================================================================
# Helpers — auto price / variants
# ============================================================================

DEFAULT_PRICE_BY_TYPE = {
    "electronic": 45.0, "clothing": 19.0, "furniture": 85.0, "appliance": 55.0,
    "jewelry": 29.0, "beauty": 15.0, "food_solid": 8.0, "toy": 22.0,
    "automotive": 40.0, "book": 12.0, "sport": 25.0, "plant": 14.0,
    "pet": 16.0, "tool": 30.0, "digital_product": 10.0, "service": 20.0,
}
DEFAULT_STOCK_PER_VARIANT = 8
DEFAULT_FLAT_STOCK = 120


def auto_price(product_type: str, product_name: str) -> float:
    base = DEFAULT_PRICE_BY_TYPE.get(product_type, 19.0)
    h = abs(hash(product_name)) % 100
    return round(base + h / 10.0, 2)


def default_options_for(variant_key: str) -> List[str]:
    return {
        "color": ["Black", "White", "Blue", "Red", "Green"],
        "size": ["S", "M", "L", "XL"],
        "material": ["Cotton", "Leather", "Metal", "Plastic"],
        "pattern": ["Solid", "Striped", "Floral"],
        "gender": ["Men", "Women", "Unisex"],
        "storage": ["64GB", "128GB", "256GB"],
        "ram": ["4GB", "8GB", "12GB"],
        "volume": ["100ml", "200ml", "500ml"],
        "weight": ["250g", "500g", "1kg"],
        "flavor": ["Original", "Vanilla", "Chocolate"],
        "scent": ["Fresh", "Floral", "Woody"],
        "skin_type": ["Normal", "Dry", "Oily"],
        "age_group": ["Kids", "Teens", "Adults"],
    }.get(variant_key, [])


# ============================================================================
# MAIN ORCHESTRATOR
# ============================================================================

class ProductUploadOrchestrator:
    def __init__(self, config: SystemConfig, config_loader: ConfigLoader):
        self.config = config
        self.config_loader = config_loader
        self.master_db = MasterAttributeDatabase(config_loader)
        self.ai = AIService(config, self.master_db)
        self.backend = BackendClient(config)
        self.csv = CSVExporter(config.OUTPUT_DIR)

    async def initialize(self):
        await self.backend.login()

    # ---- analysis ---------------------------------------------------------

    async def _analyze(self, image_path: str) -> Dict[str, Any]:
        if self.ai.available:
            allowed = list(self.config_loader.get_variants().keys())
            a = await self.ai.analyze_and_describe(image_path, allowed)
            if a:
                return a
        # Fallback: backend AI analyzer
        b = await self.backend.ai_analyze(image_path)
        if not b:
            b = {}
        category = b.get("suggested_category") or "General"
        subcategory = b.get("suggested_subcategory") or "General"
        options = b.get("variant_options", {}) or {}
        detected = {k: (", ".join(v) if isinstance(v, list) else v)
                    for k, v in options.items() if v}
        name = b.get("product_name_hint")
        if not name or len(str(name).strip()) < 3 or str(name).lower().startswith("image"):
            name = f"{subcategory} {detected.get('color', '')}".strip() or subcategory
        return {
            "product_name": name.strip() or "Product",
            "category": category,
            "subcategory": subcategory,
            "detected_attributes": detected,
            "relevant_variants": b.get("suggested_variants") or ["color"],
            "variant_options": options,
            "product_type": b.get("product_type") or self.master_db.classify_product_type(name, category, subcategory),
            "condition": "new",
            "descriptions": {},
            "source": "backend",
        }

    # ---- variant selection ----------------------------------------------

    async def _select_variants(self, analysis: Dict[str, Any], allowed: List[str]):
        category = analysis["category"]
        subcategory = analysis["subcategory"]
        detected = analysis.get("detected_attributes", {})
        backend_options = analysis.get("variant_options", {})
        relevant = [v for v in analysis.get("relevant_variants", []) if v in allowed]

        options: Dict[str, List[str]] = {}
        for k in relevant:
            if k in detected and detected[k]:
                options[k] = [x.strip() for x in str(detected[k]).split(",") if x.strip()]
            elif k in backend_options and backend_options[k]:
                options[k] = backend_options[k][:8]
        if "color" in allowed and "color" not in options:
            options["color"] = (backend_options.get("color") or default_options_for("color"))[:6]
        is_apparel = any(kw in (category + " " + subcategory).lower()
                         for kw in ["apparel", "clothing", "fashion", "shirt", "t-shirt",
                                    "pants", "dress", "jacket", "lingerie", "bralette",
                                    "bra", "underwear"])
        if is_apparel and "size" in allowed and "size" not in options:
            options["size"] = default_options_for("size")
        options = {k: v for k, v in options.items()
                   if not any(ex in options for ex in self.master_db.get_mutually_exclusive(k) if ex != k)}
        return options

    # ---- build payload ----------------------------------------------------

    def _build_payload(self, analysis: Dict[str, Any], options: Dict[str, List[str]],
                       descriptions: Dict[str, Any]):
        category = analysis["category"]
        subcategory = analysis["subcategory"]
        product_type = analysis.get("product_type") or self.master_db.classify_product_type(
            analysis["product_name"], category, subcategory)
        price = auto_price(product_type, analysis["product_name"])

        variant_keys = list(options.keys())
        variants_json = None
        if variant_keys:
            per = DEFAULT_STOCK_PER_VARIANT
            if len(variant_keys) == 1:
                k = variant_keys[0]
                variants = [{
                    "title": f"{analysis['product_name']} - {opt}", k: opt,
                    "stock": per, "price": price, "is_active": True
                } for opt in options[k]]
            else:
                combos = list(itertools.product(*[options[k] for k in variant_keys]))[:30]
                variants = [{
                    "title": " - ".join(str(c) for c in combo),
                    **{k: v for k, v in zip(variant_keys, combo)},
                    "stock": per, "price": price, "is_active": True
                } for combo in combos]
            total_stock = sum(v["stock"] for v in variants)
            variants_json = json.dumps(variants, ensure_ascii=False)
        else:
            total_stock = DEFAULT_FLAT_STOCK

        detected = analysis.get("detected_attributes", {})
        color_val = detected.get("color")
        color_val = color_val if isinstance(color_val, str) else (color_val[0] if isinstance(color_val, list) and color_val else None)
        material_val = detected.get("material")
        material_val = material_val if isinstance(material_val, str) else (material_val[0] if isinstance(material_val, list) and material_val else None)
        sizes_val = json.dumps(options["size"]) if "size" in options else None
        brand = detected.get("brand")

        fields = {
            "name": analysis["product_name"],
            "description": descriptions.get("english_description") or "",
            "price": price,
            "stock_quantity": total_stock,
            "category": category,
            "subcategory": subcategory,
            "color": color_val,
            "brand": brand if isinstance(brand, str) else None,
            "tags": f"{subcategory}, {category}",
            "sizes": sizes_val,
            "materials": material_val,
            "variants_json": variants_json,
            "is_active": True,
        }
        return fields, price, total_stock

    # ---- one product ------------------------------------------------------

    async def upload_one(self, image_path: str) -> Dict[str, Any]:
        total_start = time.time()
        logger.info("=" * 70)
        logger.info(f"🚀 UPLOADING: {os.path.basename(image_path)}")

        analysis = await self._analyze(image_path)
        allowed = self.master_db.get_allowed_variants(analysis["category"], analysis["subcategory"])
        logger.info(f"📊 Category: {analysis['category']} > {analysis['subcategory']}")

        options = await self._select_variants(analysis, allowed)
        logger.info(f"🎯 Variants: {list(options.keys())}")

        descriptions = analysis.get("descriptions") or {}
        if not descriptions.get("english_description"):
            descriptions = self._template_descriptions(analysis, options)

        fields, price, total_stock = self._build_payload(analysis, options, descriptions)

        result = await self.backend.upload_product(image_path, fields, self.config.IMAGE_TOOLS)
        backend_id = None
        if isinstance(result.get("json"), dict):
            backend_id = result["json"].get("id")
        ok = result["status"] in (200, 201)
        logger.info(f"{'✅' if ok else '❌'} Backend responded {result['status']}"
                    f"{'' if ok else ': ' + str(result['body'])[:200]}")

        sku = f"ZOZI-{datetime.now().strftime('%Y%m%d')}-{re.sub(r'[^A-Za-z0-9]', '', analysis['product_name'] or 'P')[:8].upper()}-{str(uuid.uuid4())[:4].upper()}"
        self.csv.save({
            'product_id': str(uuid.uuid4()), 'sku': sku,
            'timestamp': datetime.now().isoformat(),
            'product_name': analysis["product_name"],
            'category': analysis["category"], 'subcategory': analysis["subcategory"],
            'price_omr': price, 'stock_quantity': total_stock,
            'condition': analysis.get("condition", "new"),
            'english_title': descriptions.get("english_title", ""),
            'english_description': fields["description"],
            'arabic_title': descriptions.get("arabic_title", ""),
            'attributes': json.dumps(options, ensure_ascii=False),
            'image_path': image_path,
            'backend_status': result["status"], 'backend_id': backend_id,
        })
        logger.info(f"⏱️  Done in {time.time() - total_start:.2f}s")
        return {"image": image_path, "analysis": analysis, "ok": ok,
                "backend_id": backend_id, "status": result["status"]}

    def _template_descriptions(self, analysis, options) -> Dict[str, Any]:
        name = analysis["product_name"]
        cat = analysis["category"]
        color = options.get("color")
        color_txt = f" Available in {', '.join(color)}." if color else ""
        return {
            "english_title": f"{name} - {cat} | ZOZI Oman",
            "english_description": (
                f"High-quality {name} in the {cat} category.{color_txt} "
                f"Carefully selected for style and durability. Fast delivery across Oman. Shop now on ZOZI."
            ),
            "arabic_title": f"{name} - {cat} | زوزي عمان",
            "arabic_description": f"{name} عالي الجودة في فئة {cat}.{color_txt} توصيل سريع في عُمان.",
            "bullet_points_en": ["✅ High Quality", "✅ Fast Delivery", "✅ Secure Checkout"],
            "bullet_points_ar": ["✅ جودة عالية", "✅ توصيل سريع", "✅ دفع آمن"],
        }

    async def run_folder(self, folder: str, clean_first: bool = True, limit: int = 0) -> List[Dict[str, Any]]:
        self._limit = limit
        image_dir = Path(folder)
        exts = {".webp", ".jpg", ".jpeg", ".png", ".gif"}
        images = sorted([p for p in image_dir.iterdir()
                         if p.is_file() and p.suffix.lower() in exts])
        if not images:
            logger.warning(f"⚠️  No images found in {folder}")
            return []
        if limit:
            images = images[:limit]
        total = len(images)
        logger.info(f"📸 Found {total} image(s) in {folder}")

        if clean_first:
            await self.backend.clean_all_products()

        # ═══════════════════════════════════════════════════════════════
        # PHASE 1 — Sequential AI vision analysis (accurate detection)
        # ═══════════════════════════════════════════════════════════════
        logger.info("\n" + "=" * 70)
        logger.info(f"🔬 PHASE 1: Analyzing {total} image(s) with AI vision...")
        logger.info("=" * 70)
        analysis_cache: Dict[str, Dict[str, Any]] = {}
        for i, img in enumerate(images, 1):
            logger.info(f"\n{'#'*70}\n# ANALYSIS {i}/{total}: {img.name}\n{'#'*70}")
            try:
                analysis = await self._analyze(str(img))
                analysis_cache[str(img)] = analysis
                logger.info(f"✓ Detected: {analysis.get('product_name', '?')} "
                            f"({analysis.get('category', '?')} > {analysis.get('subcategory', '?')})")
            except Exception as e:
                logger.error(f"❌ Analysis failed for {img.name}: {e}")
                analysis_cache[str(img)] = {
                    "product_name": img.stem.replace("_", " ").title(),
                    "category": "General", "subcategory": "General",
                    "detected_attributes": {}, "relevant_variants": ["color"],
                    "variant_options": {}, "product_type": "general",
                    "condition": "new", "descriptions": {}, "source": "fallback",
                }

        # ═══════════════════════════════════════════════════════════════
        # PHASE 2 — Parallel variant selection + upload
        # ═══════════════════════════════════════════════════════════════
        logger.info("\n" + "=" * 70)
        logger.info(f"🚀 PHASE 2: Uploading {total} product(s) in parallel (concurrency={self.config.CONCURRENCY})...")
        logger.info("=" * 70)

        concurrency = self.config.CONCURRENCY
        sem = asyncio.Semaphore(concurrency)
        completed = 0

        async def _upload_one_with_cache(img_path: str) -> Dict[str, Any]:
            nonlocal completed
            async with sem:
                completed += 1
                analysis = analysis_cache.get(img_path, {})
                logger.info(f"\n{'#'*70}\n# UPLOAD {completed}/{total}: {os.path.basename(img_path)} — {analysis.get('product_name', '?')}\n{'#'*70}")
                try:
                    return await self._upload_from_analysis(img_path, analysis)
                except Exception as e:
                    logger.error(f"❌ Upload failed {os.path.basename(img_path)}: {e}", exc_info=True)
                    return {"image": img_path, "ok": False, "error": str(e)}

        tasks = [_upload_one_with_cache(str(img)) for img in images]
        results = await asyncio.gather(*tasks)
        return results

    async def _upload_from_analysis(self, image_path: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Upload a single product using pre-computed analysis (no further AI calls)."""
        total_start = time.time()
        allowed = self.master_db.get_allowed_variants(analysis["category"], analysis["subcategory"])
        options = await self._select_variants(analysis, allowed)
        descriptions = analysis.get("descriptions") or {}
        if not descriptions.get("english_description"):
            descriptions = self._template_descriptions(analysis, options)
        fields, price, total_stock = self._build_payload(analysis, options, descriptions)
        result = await self.backend.upload_product(image_path, fields, self.config.IMAGE_TOOLS)
        backend_id = None
        if isinstance(result.get("json"), dict):
            backend_id = result["json"].get("id")
        ok = result["status"] in (200, 201)
        logger.info(f"{'✅' if ok else '❌'} {os.path.basename(image_path)} → {result['status']}"
                    f"{'' if ok else ': ' + str(result['body'])[:200]}")

        sku = f"ZOZI-{datetime.now().strftime('%Y%m%d')}-{re.sub(r'[^A-Za-z0-9]', '', analysis['product_name'] or 'P')[:8].upper()}-{str(uuid.uuid4())[:4].upper()}"
        self.csv.save({
            'product_id': str(uuid.uuid4()), 'sku': sku,
            'timestamp': datetime.now().isoformat(),
            'product_name': analysis["product_name"],
            'category': analysis["category"], 'subcategory': analysis["subcategory"],
            'price_omr': price, 'stock_quantity': total_stock,
            'condition': analysis.get("condition", "new"),
            'english_title': descriptions.get("english_title", ""),
            'english_description': fields["description"],
            'arabic_title': descriptions.get("arabic_title", ""),
            'attributes': json.dumps(options, ensure_ascii=False),
            'image_path': image_path,
            'backend_status': result["status"], 'backend_id': backend_id,
        })
        logger.info(f"⏱️  Done in {time.time() - total_start:.2f}s")
        return {"image": image_path, "analysis": analysis, "ok": ok,
                "backend_id": backend_id, "status": result["status"]}

    async def close(self):
        await self.ai.close()
        await self.backend.close()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def parse_args():
    p = argparse.ArgumentParser(description="ZOZI automatic AI product uploader")
    here = Path(__file__).resolve().parent
    default_folder = str(here.parents[1] / "image")
    p.add_argument("--folder", default=default_folder)
    p.add_argument("--email", default=SystemConfig.SUPPLIER_EMAIL)
    p.add_argument("--password", default=SystemConfig.SUPPLIER_PASSWORD)
    p.add_argument("--backend", default=SystemConfig.BACKEND_URL)
    p.add_argument("--no-clean", action="store_true")
    p.add_argument("--config", default=str(here / "zozi_variant_config.json"))
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--no-ollama", action="store_true",
                   help="Skip Ollama and use fast backend AI analyzer instead")
    p.add_argument("--concurrency", type=int, default=3,
                   help="Number of parallel uploads (default: 3)")
    return p.parse_args()


async def main():
    args = parse_args()
    await SystemConfig.validate()

    config = SystemConfig(
        BACKEND_URL=args.backend,
        SUPPLIER_EMAIL=args.email,
        SUPPLIER_PASSWORD=args.password,
        USE_OLLAMA=not args.no_ollama,
        CONCURRENCY=args.concurrency,
    )
    config_loader = ConfigLoader(args.config)

    mode = "Backend AI Analyzer (fast)" if args.no_ollama else "Ollama AI (accurate detection)"
    logger.info("\n" + "=" * 70)
    logger.info(f"🧪 ZOZI AUTOMATIC AI PRODUCT UPLOAD ENGINE [Mode: {mode}, Concurrency: {args.concurrency}]")
    logger.info("=" * 70)

    orchestrator = ProductUploadOrchestrator(config, config_loader)
    try:
        await orchestrator.initialize()
        results = await orchestrator.run_folder(args.folder, clean_first=not args.no_clean, limit=args.limit)
        ok = sum(1 for r in results if r.get("ok"))
        failed = [r for r in results if not r.get("ok")]
        logger.info("\n" + "=" * 70)
        logger.info(f"🎉 FINISHED: {ok}/{len(results)} uploaded successfully")
        if failed:
            for f in failed:
                logger.warning(f"   ❌ {os.path.basename(f.get('image','?'))}: {f.get('error','unknown')}")
        logger.info("=" * 70)
    except Exception as e:
        logger.error(f"❌ Fatal: {e}", exc_info=True)
    finally:
        await orchestrator.close()


if __name__ == "__main__":
    asyncio.run(main())
