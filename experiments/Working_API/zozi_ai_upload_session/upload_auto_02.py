#!/usr/bin/env python3
"""
ZOZI AI Product Upload System - 100% FREE with Dynamic Variants
================================================================
✅ Automatic Image Detection (Moondream Vision + Qwen2.5)
✅ Dynamic Variant Detection (AI decides what variants to ask for)
✅ Smart Rule-Based Interview (Only asks relevant questions)
✅ Ollama AI (Runs on YOUR computer)
"""

import os
import json
import csv
import uuid
import re
import base64
import itertools
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================
# CONFIGURATION
# ============================================
class Config:
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5"
    OLLAMA_VISION_MODEL: str = "moondream"
    OUTPUT_DIR: str = "products_output"
    
    @classmethod
    async def validate(cls):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{cls.OLLAMA_BASE_URL}/api/tags")
                if response.status_code != 200: raise ConnectionError("Ollama is not responding")
                models = [m.get("name", "").split(":")[0] for m in response.json().get("models", [])]
                if cls.OLLAMA_VISION_MODEL not in models: raise ValueError(f"Run: ollama pull {cls.OLLAMA_VISION_MODEL}")
                if cls.OLLAMA_MODEL not in models: raise ValueError(f"Run: ollama pull {cls.OLLAMA_MODEL}")
                logger.info(f"✅ Ollama running: {cls.OLLAMA_MODEL} + {cls.OLLAMA_VISION_MODEL}")
        except httpx.ConnectError:
            raise ConnectionError("❌ Ollama is not running!")

# ============================================
# AI SERVICES (Vision + Formatting + Variant Detection)
# ============================================
class AIService:
    """Handles all AI interactions"""
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=f"{Config.OLLAMA_BASE_URL}/v1",
            headers={"Content-Type": "application/json"},
            timeout=300.0
        )

    def encode_image(self, image_path: str) -> str:
        with open(image_path, "rb") as f: return base64.b64encode(f.read()).decode("utf-8")

    async def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Step 1: Vision AI sees the image, Text AI formats it."""
        logger.info(f"🔍 Analyzing image: {os.path.basename(image_path)}")
        image_base64 = self.encode_image(image_path)
        
        vision_prompt = "Look at this product. What is the exact product name, brand, category, color, and condition? Be brief."
        try:
            res = await self.client.post("/chat/completions", json={
                "model": Config.OLLAMA_VISION_MODEL,
                "messages": [{"role": "user", "content": [
                    {"type": "text", "text": vision_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]}], "temperature": 0.3, "stream": False
            })
            raw_desc = res.json()["choices"][0]["message"]["content"]
            logger.info(f"👁️ Vision saw: {raw_desc.strip()}")

            format_prompt = f"""Extract details from: "{raw_desc}"
Return ONLY raw JSON (no markdown):
{{
  "product_name": "Exact item name (e.g., Wristwatch, T-Shirt)",
  "category": "Electronics/Fashion/Home/Beauty/Sports/Books/Groceries/General",
  "subcategory": "Specific type",
  "detected_attributes": {{"brand": "", "color": "", "model": ""}},
  "condition": "new or used"
}}"""
            res2 = await self.client.post("/chat/completions", json={
                "model": Config.OLLAMA_MODEL, "messages": [{"role": "user", "content": format_prompt}],
                "temperature": 0.1, "stream": False, "options": {"num_predict": 512}
            })
            content = res2.json()["choices"][0]["message"]["content"].strip()
            if "```" in content: content = re.sub(r'```[a-zA-Z]*\n?', '', content)
            
            json_match = re.search(r'\{[\s\S]*\}', content)
            analysis = json.loads(json_match.group(), strict=False) if json_match else json.loads(content, strict=False)
            
            if not analysis.get("product_name") or len(analysis["product_name"].strip()) < 3:
                analysis["product_name"] = " ".join(raw_desc.split()[:4]).capitalize()
                
            analysis.setdefault("category", "General")
            analysis.setdefault("subcategory", "General")
            analysis.setdefault("detected_attributes", {})
            analysis.setdefault("condition", "new")
            
            logger.info(f"✓ Detected: {analysis['product_name']} ({analysis['category']})")
            return analysis
        except Exception as e:
            logger.error(f"❌ Vision failed: {e}")
            return await self._manual_fallback(image_path)

    async def determine_relevant_variants(self, product_name: str, category: str, subcategory: str) -> List[str]:
        """Step 2: AI decides what variants are relevant for this specific product."""
        logger.info("🧠 Determining relevant product variants...")
        prompt = f"""Based on the product "{product_name}" ({category} > {subcategory}), what variant options must a customer select when buying this online?
Choose from: "color", "size", "storage", "model", "material", "scent", "flavor", "strap_type", "capacity", "none".
Return ONLY raw JSON: {{"relevant_variants": ["variant1", "variant2"]}}"""
        
        try:
            res = await self.client.post("/chat/completions", json={
                "model": Config.OLLAMA_MODEL, "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1, "stream": False, "options": {"num_predict": 256}
            })
            content = res.json()["choices"][0]["message"]["content"].strip()
            if "```" in content: content = re.sub(r'```[a-zA-Z]*\n?', '', content)
            json_match = re.search(r'\{[\s\S]*\}', content)
            result = json.loads(json_match.group(), strict=False) if json_match else json.loads(content, strict=False)
            variants = result.get("relevant_variants", ["color"])
            if "none" in variants: variants = []
            logger.info(f"✓ Relevant variants: {variants}")
            return variants
        except Exception as e:
            logger.error(f"❌ Variant detection failed: {e}. Defaulting to ['color']")
            return ["color"]

    async def generate_descriptions(self, product_data: Dict, image_analysis: Dict) -> Dict[str, Any]:
        """Step 4: Generate SEO descriptions."""
        logger.info(f"✍️ Generating descriptions...")
        product_name = image_analysis.get("product_name", "Product")
        category = image_analysis.get("category", "General")
        price = product_data.get('price_omr', 0)
        
        attr_list = [f"{k}: {v}" for k, v in product_data.get("attributes", {}).items() if k not in ["variant_stock", "color", "size"]]
        if "color" in product_data.get("attributes", {}): attr_list.append(f"colors: {', '.join(product_data['attributes']['color'])}")
        if "size" in product_data.get("attributes", {}): attr_list.append(f"sizes: {', '.join(product_data['attributes']['size'])}")
        features_text = ", ".join(attr_list)

        prompt = f"""Create listing for: {product_name} ({category}). Price: {price} OMR. Features: {features_text}.
Return JSON:
{{
  "english_title": "Short SEO title", "english_description": "Desc with ✅ bullets",
  "arabic_title": "عنوان بالعربية", "arabic_description": "وصف بالعربية مع ✅",
  "bullet_points_en": ["✅ 1", "✅ 2"], "bullet_points_ar": ["✅ ١", "✅ ٢"],
  "meta_title_en": "SEO title", "meta_description_en": "SEO desc",
  "meta_title_ar": "عنوان SEO", "meta_description_ar": "وصف SEO"
}}"""
        try:
            res = await self.client.post("/chat/completions", json={
                "model": Config.OLLAMA_MODEL, "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7, "stream": False, "options": {"num_predict": 1024}
            })
            content = res.json()["choices"][0]["message"]["content"].strip()
            if "```" in content: content = re.sub(r'```[a-zA-Z]*\n?', '', content)
            json_match = re.search(r'\{[\s\S]*\}', content)
            return json.loads(json_match.group(), strict=False) if json_match else json.loads(content, strict=False)
        except Exception as e:
            logger.error(f"❌ Desc error: {e}. Using fallback.")
            return self._fallback_desc(product_data, image_analysis)

    async def _manual_fallback(self, image_path: str) -> Dict[str, Any]:
        print("\n📝 MANUAL INPUT (Vision failed)")
        return {
            "product_name": input("📦 Product name: ").strip(),
            "category": input("📂 Category: ").strip() or "General",
            "subcategory": input("📂 Subcategory: ").strip() or "General",
            "detected_attributes": {"brand": input("🏷️ Brand: ").strip(), "color": input("🎨 Color: ").strip()},
            "condition": input("📋 Condition (new/used) [new]: ").strip() or "new"
        }

    def _fallback_desc(self, product_data: Dict, image_analysis: Dict) -> Dict[str, Any]:
        name = image_analysis.get("product_name", "Product")
        cat = image_analysis.get("category", "General")
        return {
            "english_title": f"{name} - {cat} | ZOZI", "english_description": f"High quality {name} at ZOZI.",
            "arabic_title": f"{name} - {cat} | زوزي", "arabic_description": f"{name} عالي الجودة في زوزي.",
            "bullet_points_en": ["✅ High Quality", "✅ Fast Delivery"], "bullet_points_ar": ["✅ جودة عالية", "✅ توصيل سريع"],
            "meta_title_en": f"{name} | ZOZI", "meta_description_en": f"Buy {name} online.",
            "meta_title_ar": f"{name} | زوزي", "meta_description_ar": f"اشتري {name} أونلاين."
        }

    async def close(self): await self.client.aclose()

# ============================================
# SMART INTERVIEW (Dynamic Variants)
# ============================================
class SmartInterviewService:
    def __init__(self): pass

    async def conduct_interview(self, image_analysis: Dict, relevant_variants: List[str]) -> Dict[str, Any]:
        logger.info("💬 Starting smart interview...")
        category = image_analysis.get("category", "General")
        product_name = image_analysis.get("product_name", "Product")
        
        print("\n" + "=" * 70)
        print(f"💬 INTERVIEW FOR: {product_name} ({category})")
        print(f"🎯 AI determined relevant variants: {relevant_variants}")
        print("=" * 70)
        
        collected_data = {"condition": image_analysis.get("condition", "new")}
        attributes = image_analysis.get("detected_attributes", {}).copy()

        # 1. Price & Stock
        while True:
            try:
                price = float(input(f"\n💰 Price in OMR: ").strip())
                if price > 0: collected_data["price_omr"] = price; break
                print("❌ Must be > 0")
            except ValueError: print("❌ Invalid number")

        while True:
            try:
                stock_str = input(f"📦 Total Stock (or Enter to calculate later): ").strip()
                if not stock_str: collected_data["stock_quantity"] = 0; break
                stock = int(stock_str)
                if stock >= 0: collected_data["stock_quantity"] = stock; break
                print("❌ Cannot be negative")
            except ValueError: print("❌ Invalid number")

        # 2. Dynamic Variant Questions
        if relevant_variants:
            print("\n🎨 Product Variants:")
            
            # Colors (FIXED: Key is now "color" to match relevant_variants)
            if "color" in relevant_variants:
                colors_input = input("🎨 Available colors (comma-separated, e.g., Black, White): ").strip()
                if colors_input: attributes["color"] = [c.strip().title() for c in colors_input.split(',')]

            # Sizes (FIXED: Key is now "size" to match relevant_variants)
            if "size" in relevant_variants:
                sizes_input = input("📏 Available sizes (comma-separated, e.g., S, M, L or 40, 41): ").strip()
                if sizes_input: attributes["size"] = [s.strip().upper() for s in sizes_input.split(',')]

            # Other specific variants
            variant_prompts = {
                "storage": "💾 Storage options (comma-sep, e.g., 128GB, 256GB): ",
                "model": "📦 Available models/versions (comma-sep): ",
                "material": "🧵 Available materials (comma-sep, e.g., Cotton, Leather): ",
                "scent": "🌸 Available scents (comma-sep): ",
                "flavor": "🍓 Available flavors (comma-sep): ",
                "strap_type": "⌚ Strap types (comma-sep, e.g., Leather, Metal, Silicone): ",
                "capacity": "📦 Capacity options in Liters (comma-sep, e.g., 200L, 300L): "
            }

            for var in relevant_variants:
                if var in variant_prompts and var not in ["color", "size"]:
                    val = input(variant_prompts[var]).strip()
                    if val: attributes[var] = [v.strip() for v in val.split(',')]

            # 3. Variant Stock Matrix (If multiple variants exist)
            # Now correctly includes "color" and "size" because the keys match!
            variant_types = [v for v in relevant_variants if v in attributes and isinstance(attributes[v], list)]
            
            if len(variant_types) >= 2:
                print("\n📦 Stock Distribution:")
                print("1. Same stock for all variants (Use total entered above)")
                print("2. Different stock for each combination (Matrix)")
                if input("Enter 1 or 2 [1]: ").strip() == "2":
                    variant_stock = {}
                    total = 0
                    combinations = list(itertools.product(*[attributes[v] for v in variant_types]))
                    
                    for combo in combinations:
                        combo_name = " - ".join(combo)
                        while True:
                            qty = input(f"  🔹 {combo_name}: ").strip()
                            if not qty: variant_stock[combo_name] = 0; break
                            if qty.isdigit(): variant_stock[combo_name] = int(qty); total += int(qty); break
                            print("    ❌ Enter a number or press Enter for 0.")
                    
                    collected_data["stock_quantity"] = total
                    attributes["variant_stock"] = variant_stock
                    logger.info(f"✓ Total stock updated from matrix: {total}")

            elif len(variant_types) == 1 and "color" in variant_types:
                print("\n📦 Stock per Color:")
                variant_stock = {}
                total = 0
                for color in attributes["color"]: # FIXED: Now correctly looks for "color"
                    while True:
                        qty = input(f"  🔹 {color}: ").strip()
                        if not qty: variant_stock[color] = 0; break
                        if qty.isdigit(): variant_stock[color] = int(qty); total += int(qty); break
                        print("    ❌ Enter a number or press Enter for 0.")
                collected_data["stock_quantity"] = total
                attributes["variant_stock"] = variant_stock
                logger.info(f"✓ Total stock updated from colors: {total}")

        collected_data["attributes"] = attributes
        logger.info("✓ Interview complete")
        return collected_data

# ============================================
# DATA SAVER & ORCHESTRATOR
# ============================================
class DataSaver:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir); self.output_dir.mkdir(exist_ok=True)
        self.filepath = self.output_dir / "zozi_products.csv"
        self.fieldnames = ['product_id', 'sku', 'timestamp', 'product_name', 'category', 'subcategory',
            'price_omr', 'stock_quantity', 'condition', 'english_title', 'english_description',
            'arabic_title', 'arabic_description', 'bullet_points_en', 'bullet_points_ar',
            'meta_title_en', 'meta_description_en', 'meta_title_ar', 'meta_description_ar',
            'attributes', 'image_paths', 'supplier_id', 'status']

    def save_product(self, product_data, descriptions, image_analysis, image_paths, supplier_id):
        product_id = str(uuid.uuid4())
        sku = f"ZOZI-{datetime.now().strftime('%Y%m%d')}-{re.sub(r'[^A-Za-z0-9]', '', product_data.get('english_title', 'P'))[:8].upper()}-{str(uuid.uuid4())[:4].upper()}"
        row = {
            'product_id': product_id, 'sku': sku, 'timestamp': datetime.now().isoformat(),
            'product_name': image_analysis.get('product_name', ''), 'category': image_analysis.get('category', ''),
            'subcategory': image_analysis.get('subcategory', ''), 'price_omr': product_data.get('price_omr', 0.0),
            'stock_quantity': product_data.get('stock_quantity', 0), 'condition': product_data.get('condition', 'new'),
            'english_title': descriptions.get('english_title', ''), 'english_description': descriptions.get('english_description', ''),
            'arabic_title': descriptions.get('arabic_title', ''), 'arabic_description': descriptions.get('arabic_description', ''),
            'bullet_points_en': json.dumps(descriptions.get('bullet_points_en', []), ensure_ascii=False),
            'bullet_points_ar': json.dumps(descriptions.get('bullet_points_ar', []), ensure_ascii=False),
            'meta_title_en': descriptions.get('meta_title_en', ''), 'meta_description_en': descriptions.get('meta_description_en', ''),
            'meta_title_ar': descriptions.get('meta_title_ar', ''), 'meta_description_ar': descriptions.get('meta_description_ar', ''),
            'attributes': json.dumps(product_data.get('attributes', {}), ensure_ascii=False),
            'image_paths': '|'.join(image_paths), 'supplier_id': supplier_id, 'status': 'draft'
        }
        file_exists = self.filepath.exists()
        with open(self.filepath, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            if not file_exists: writer.writeheader()
            writer.writerow(row)
        logger.info(f"✅ Saved to {self.filepath}")
        return product_id

class ProductUploadOrchestrator:
    def __init__(self):
        self.ai = AIService()
        self.interview = SmartInterviewService()
        self.saver = DataSaver(Config.OUTPUT_DIR)

    async def upload_product(self, image_paths: List[str], supplier_id: str):
        logger.info("=" * 70); logger.info("🚀 STARTING ZOZI PRODUCT UPLOAD"); logger.info("=" * 70)
        
        logger.info("\n🔍 STEP 1: Analyzing image...")
        image_analysis = await self.ai.analyze_image(image_paths[0])
        
        logger.info("\n🎯 STEP 2: Detecting relevant variants...")
        relevant_variants = await self.ai.determine_relevant_variants(
            image_analysis.get("product_name"), 
            image_analysis.get("category"), 
            image_analysis.get("subcategory")
        )
        
        logger.info("\n💬 STEP 3: Conducting interview...")
        collected_data = await self.interview.conduct_interview(image_analysis, relevant_variants)
        
        logger.info("\n✍️ STEP 4: Generating descriptions...")
        descriptions = await self.ai.generate_descriptions(collected_data, image_analysis)
        
        logger.info("\n" + "=" * 70); logger.info("📋 PRODUCT SUMMARY"); logger.info("=" * 70)
        logger.info(f"Name (EN): {descriptions.get('english_title')}")
        logger.info(f"Name (AR): {descriptions.get('arabic_title')}")
        logger.info(f"Category: {image_analysis.get('category')} > {image_analysis.get('subcategory')}")
        logger.info(f"Price: {collected_data.get('price_omr')} OMR | Stock: {collected_data.get('stock_quantity')}")
        logger.info(f"Variants Asked: {relevant_variants}")
        logger.info(f"Attributes: {json.dumps(collected_data.get('attributes', {}), indent=2, ensure_ascii=False)}")
        logger.info("=" * 70)
        
        logger.info("\n💾 STEP 5: Saving...")
        product_id = self.saver.save_product(collected_data, descriptions, image_analysis, image_paths, supplier_id)
        
        logger.info("\n" + "=" * 70); logger.info("✅ COMPLETE!"); logger.info("=" * 70)
        logger.info(f"Product ID: {product_id} | CSV: {self.saver.filepath}")
        return {'product_id': product_id, 'product_data': collected_data, 'image_analysis': image_analysis, 'descriptions': descriptions}

    async def close(self): await self.ai.close()

# ============================================
# MAIN
# ============================================
async def test_upload():
    try: await Config.validate()
    except Exception as e: print(f"\n❌ {e}"); return

    print("\n" + "=" * 70); print("🧪 ZOZI PRODUCT UPLOAD SYSTEM - TEST"); print("=" * 70)
    path = input("\n📸 Enter product image path: ").strip().strip('"').strip("'")
    if not path or not os.path.exists(path): print(f"❌ File not found: {path}"); return
    
    supplier_id = input("\n👤 Supplier ID [supplier_001]: ").strip() or "supplier_001"
    orchestrator = ProductUploadOrchestrator()
    
    try:
        result = await orchestrator.upload_product([path], supplier_id)
        print("\n" + "=" * 70); print("🎉 SUCCESS!"); print("=" * 70)
        print(f"✅ ID: {result['product_id']} | Product: {result['descriptions'].get('english_title')}")
        print(f"✅ Category: {result['image_analysis'].get('category')} | Price: {result['product_data'].get('price_omr')} OMR")
        print("=" * 70)
    except Exception as e: logger.error(f"❌ Error: {str(e)}", exc_info=True)
    finally: await orchestrator.close()

if __name__ == "__main__":
    import asyncio
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║   🚀 ZOZI Product Upload System (Dynamic Variants)       ║
    ║   ✅ AI detects exactly which variants to ask for!       ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    asyncio.run(test_upload())