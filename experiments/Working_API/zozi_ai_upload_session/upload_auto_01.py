#!/usr/bin/env python3
"""
ZOZI AI Product Upload System - 100% FREE with Vision AI & Variant Matrix
==========================================================================
✅ Automatic Image Detection (Moondream Vision + Qwen2.5 Formatting)
✅ Smart Rule-Based Interview (With Color/Size Variant Matrix)
✅ Ollama AI (Runs on YOUR computer)
✅ No API keys, no credit cards, no internet needed
"""

import os
import json
import csv
import uuid
import re
import base64
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================
# CONFIGURATION
# ============================================

class Config:
    """Configuration for services"""
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5"          # For text/descriptions/formatting
    OLLAMA_VISION_MODEL: str = "moondream" # For image analysis
    OUTPUT_DIR: str = "products_output"
    
    @classmethod
    async def validate(cls):
        """Validate Ollama is running"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{cls.OLLAMA_BASE_URL}/api/tags")
                if response.status_code != 200:
                    raise ConnectionError("Ollama is not responding")
                
                models = response.json().get("models", [])
                model_names = [m.get("name", "").split(":")[0] for m in models]
                
                if cls.OLLAMA_VISION_MODEL not in model_names:
                    raise ValueError(f"Vision model '{cls.OLLAMA_VISION_MODEL}' not installed. Run: ollama pull {cls.OLLAMA_VISION_MODEL}")
                if cls.OLLAMA_MODEL not in model_names:
                    raise ValueError(f"Text model '{cls.OLLAMA_MODEL}' not installed. Run: ollama pull {cls.OLLAMA_MODEL}")
                
                logger.info(f"✅ Ollama is running with models: {cls.OLLAMA_MODEL} + {cls.OLLAMA_VISION_MODEL}")
                return True
                
        except httpx.ConnectError:
            raise ConnectionError("❌ Ollama is not running! Please start the Ollama application.")


# ============================================
# IMAGE RECOGNITION SERVICE (Vision AI)
# ============================================

class ImageRecognitionService:
    """Automatic product detection using Ollama Vision"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=f"{Config.OLLAMA_BASE_URL}/v1",
            headers={"Content-Type": "application/json"},
            timeout=300.0
        )
    
    def encode_image(self, image_path: str) -> str:
        """Convert image to base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    async def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Two-step analysis: Vision model sees it, Text model formats it"""
        logger.info(f"🔍 Analyzing image with AI vision: {os.path.basename(image_path)}")
        
        image_base64 = self.encode_image(image_path)
        vision_prompt = "Look at this product image. What is the exact product name, brand, category, color, and condition (new or used)? Be brief."
        
        try:
            # STEP 1: Vision Model
            response = await self.client.post("/chat/completions", json={
                "model": Config.OLLAMA_VISION_MODEL,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": vision_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                    ]
                }],
                "temperature": 0.3,
                "stream": False
            })
            response.raise_for_status()
            raw_description = response.json()["choices"][0]["message"]["content"]
            logger.info(f"👁️ Vision AI saw: {raw_description.strip()}")
            
            # STEP 2: Text Model formats to JSON (with strict product name rule)
            logger.info("🧠 Formatting vision output into JSON...")
            json_prompt = f"""Analyze this product description and extract the details into JSON.
Description: "{raw_description}"

CRITICAL RULES:
1. "product_name" MUST be the actual item (e.g., T-Shirt, Wristwatch, Refrigerator). NEVER leave it empty!
2. "category" MUST be one of: Electronics, Fashion, Home, Beauty, Sports, Books, Groceries, General.
3. Return ONLY raw JSON. No markdown (```json), no explanations.

JSON Format:
{{
  "product_name": "Exact product name",
  "category": "Main category",
  "subcategory": "Specific type",
  "detected_attributes": {{
    "brand": "Brand or empty string",
    "color": "Color or empty string",
    "model": "Model or empty string"
  }},
  "condition": "new or used"
}}"""

            json_response = await self.client.post("/chat/completions", json={
                "model": Config.OLLAMA_MODEL,
                "messages": [{"role": "user", "content": json_prompt}],
                "temperature": 0.1,
                "stream": False,
                "options": {"num_predict": 512}
            })
            json_response.raise_for_status()
            content = json_response.json()["choices"][0]["message"]["content"]
            
            # Clean up markdown and parse JSON safely (strict=False prevents crashes)
            content = content.strip()
            if "```" in content:
                content = re.sub(r'```[a-zA-Z]*\n?', '', content)
            
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                analysis = json.loads(json_match.group(), strict=False)
            else:
                raise ValueError("Could not find JSON in response")
                
            # Ensure all fields exist and product name is not empty
            analysis.setdefault("category", "General")
            analysis.setdefault("subcategory", "General")
            analysis.setdefault("detected_attributes", {})
            analysis.setdefault("condition", "new")
            
            if not analysis.get("product_name") or len(analysis["product_name"].strip()) < 3:
                # Fallback: Extract noun from raw description
                words = raw_description.split()
                analysis["product_name"] = " ".join(words[:4]).strip().capitalize()
            
            logger.info(f"✓ AI Detected: {analysis['product_name']} ({analysis['category']})")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Vision AI failed: {e}")
            logger.warning("⚠️  Falling back to manual input")
            return await self._manual_input_fallback(image_path)
    
    async def _manual_input_fallback(self, image_path: str) -> Dict[str, Any]:
        """Fallback to manual input if vision fails"""
        print("\n" + "=" * 70)
        print("📝 MANUAL PRODUCT DESCRIPTION (Vision AI failed)")
        print("=" * 70)
        
        product_name = input("\n📦 Product name: ").strip()
        category = input("📂 Category: ").strip() or "General"
        subcategory = input("📂 Subcategory: ").strip() or "General"
        brand = input("🏷️ Brand: ").strip()
        color = input("🎨 Color: ").strip()
        condition = input("📋 Condition (new/used) [new]: ").strip() or "new"
        
        detected_attributes = {}
        if brand: detected_attributes["brand"] = brand
        if color: detected_attributes["color"] = color
        
        return {
            "product_name": product_name,
            "category": category,
            "subcategory": subcategory,
            "detected_attributes": detected_attributes,
            "condition": condition
        }
    
    async def close(self):
        await self.client.aclose()


# ============================================
# SMART INTERVIEW SERVICE (With Variant Matrix)
# ============================================

class SmartInterviewService:
    """Rule-based interview system with comprehensive variant support"""
    
    def __init__(self):
        pass
    
    async def conduct_interview(self, image_analysis: Dict) -> Dict[str, Any]:
        """Conduct smart interview based on detected product type"""
        logger.info("💬 Starting smart interview...")
        
        category = image_analysis.get("category", "General")
        product_name = image_analysis.get("product_name", "Product")
        
        print("\n" + "=" * 70)
        print(f"💬 INTERVIEW FOR: {product_name} ({category})")
        print("=" * 70)
        
        collected_data = {
            "condition": image_analysis.get("condition", "new")
        }
        
        # Always ask for price
        while True:
            try:
                price = input(f"\n💰 Price in OMR (Omani Rials): ").strip()
                price = float(price)
                if price > 0:
                    collected_data["price_omr"] = price
                    break
                print("❌ Price must be greater than 0")
            except ValueError:
                print("❌ Please enter a valid number")
        
        # Ask for initial stock (might be overridden by variant matrix)
        while True:
            try:
                stock = input(f"📦 Total Stock quantity (or press Enter to calculate from variants later): ").strip()
                if not stock:
                    collected_data["stock_quantity"] = 0
                    break
                stock = int(stock)
                if stock >= 0:
                    collected_data["stock_quantity"] = stock
                    break
                print("❌ Stock cannot be negative")
            except ValueError:
                print("❌ Please enter a valid number")
        
        # Category-specific questions
        attributes = image_analysis.get("detected_attributes", {}).copy()
        
        # Broad matching for Fashion/Apparel/Shoes
        is_apparel = category in ["Fashion", "Clothing", "Apparel"] or \
                     any(kw in image_analysis.get("subcategory", "").lower() for kw in ["shirt", "shoe", "dress", "pants", "t-shirt"])
        
        if is_apparel:
            print("\n👕 Product Variants (Sizes & Colors):")
            
            # Colors
            colors_input = input("🎨 Available colors (comma-separated, e.g., Black, White, Red): ").strip()
            colors = [c.strip().title() for c in colors_input.split(',') if c.strip()]
            if colors:
                attributes["colors"] = colors
            
            # Sizes
            sizes_input = input("📏 Available sizes (comma-separated, e.g., S, M, L, XL or 40, 41, 42): ").strip()
            sizes = [s.strip().upper() for s in sizes_input.split(',') if s.strip()]
            if sizes:
                attributes["sizes"] = sizes
            
            # Gender
            gender = input("👤 Gender (Men/Women/Unisex) [Unisex]: ").strip() or "Unisex"
            attributes["gender"] = gender
            
            # Material
            material = input("🧵 Material (Cotton, Polyester, Leather, etc.): ").strip()
            if material:
                attributes["material"] = material
            
            # Color-wise size matrix
            if colors and sizes:
                print("\n📦 Stock Distribution:")
                print("1. Same sizes available in all colors (Use total stock entered above)")
                print("2. Different stock for each color/size (Color-wise size matrix)")
                dist = input("Enter 1 or 2 [1]: ").strip() or "1"
                
                if dist == "2":
                    variant_stock = {}
                    total_variant_stock = 0
                    for color in colors:
                        print(f"\n  🔹 Stock for {color}:")
                        for size in sizes:
                            while True:
                                qty = input(f"    {size}: ").strip()
                                if not qty:
                                    variant_stock[f"{color}-{size}"] = 0
                                    break
                                if qty.isdigit():
                                    variant_stock[f"{color}-{size}"] = int(qty)
                                    total_variant_stock += int(qty)
                                    break
                                print("    ❌ Please enter a number or press Enter for 0.")
                    
                    # Update total stock based on variants
                    collected_data["stock_quantity"] = total_variant_stock
                    attributes["variant_stock"] = variant_stock
                    logger.info(f"✓ Total stock updated from variants: {total_variant_stock}")

        elif category == "Electronics":
            print("\n📱 Electronics Details:")
            if "phone" in image_analysis.get("subcategory", "").lower() or "mobile" in product_name.lower():
                storage = input("💾 Storage (e.g., 128GB, 256GB) [128GB]: ").strip() or "128GB"
                attributes["storage"] = storage
                if collected_data.get("condition") == "used":
                    battery = input("🔋 Battery health % (e.g., 85) [90]: ").strip() or "90"
                    attributes["battery_health"] = f"{battery}%"
            else:
                model = input("📦 Model/Specs: ").strip()
                if model: attributes["model"] = model

        elif category == "Beauty":
            print("\n💄 Beauty Product Details:")
            volume = input("📦 Volume (e.g., 50ml, 100ml): ").strip()
            if volume: attributes["volume"] = volume

        elif category == "Home":
            print("\n🏠 Home Product Details:")
            dimensions = input("📐 Dimensions (L x W x H in cm): ").strip()
            if dimensions: attributes["dimensions"] = dimensions
            material = input("🪵 Material (Steel, Wood, Plastic, etc.): ").strip()
            if material: attributes["material"] = material
        
        collected_data["attributes"] = attributes
        logger.info("✓ Interview complete")
        return collected_data


# ============================================
# AI DESCRIPTION GENERATOR (Ollama)
# ============================================

class DescriptionGenerator:
    """Generate SEO-optimized descriptions using Ollama"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=f"{Config.OLLAMA_BASE_URL}/v1",
            headers={"Content-Type": "application/json"},
            timeout=300.0
        )
    
    async def generate_descriptions(self, product_data: Dict, image_analysis: Dict) -> Dict[str, Any]:
        """Generate SEO-optimized descriptions in English and Arabic"""
        logger.info(f"✍️ Generating product descriptions with Ollama ({Config.OLLAMA_MODEL})...")
        
        product_name = image_analysis.get("product_name", "Product")
        category = image_analysis.get("category", "General")
        price = product_data.get('price_omr', 0)
        attributes = product_data.get("attributes", {})
        
        # Format attributes nicely
        attr_list = []
        for k, v in attributes.items():
            if k not in ["variant_stock", "colors", "sizes"]: # Skip complex arrays for prompt
                attr_list.append(f"{k}: {v}")
        if "colors" in attributes:
            attr_list.append(f"colors: {', '.join(attributes['colors'])}")
        if "sizes" in attributes:
            attr_list.append(f"sizes: {', '.join(attributes['sizes'])}")
            
        features_text = ", ".join(attr_list)
        
        prompt = f"""Create product listing for: {product_name}
Category: {category}
Price: {price} OMR
Features: {features_text}

Return JSON:
{{
  "english_title": "Short SEO title",
  "english_description": "Brief description with ✅ bullets",
  "arabic_title": "عنوان بالعربية",
  "arabic_description": "وصف بالعربية مع ✅",
  "bullet_points_en": ["✅ Point 1", "✅ Point 2"],
  "bullet_points_ar": ["✅ نقطة ١", "✅ نقطة ٢"],
  "meta_title_en": "SEO title",
  "meta_description_en": "SEO description",
  "meta_title_ar": "عنوان SEO",
  "meta_description_ar": "وصف SEO"
}}"""
        
        try:
            response = await self.client.post("/chat/completions", json={
                "model": Config.OLLAMA_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "stream": False,
                "options": {"num_predict": 1024, "num_ctx": 2048}
            })
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            
            # Clean up markdown and parse safely
            content = content.strip()
            if "```" in content:
                content = re.sub(r'```[a-zA-Z]*\n?', '', content)
            
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                result = json.loads(json_match.group(), strict=False) # strict=False prevents crashes
            else:
                result = json.loads(content, strict=False)
            
            logger.info("✓ Descriptions generated successfully")
            return result
            
        except Exception as e:
            logger.error(f"❌ Ollama error: {e}")
            logger.warning("⚠️  Using fallback template descriptions")
            return self._fallback_descriptions(product_data, image_analysis)
    
    def _fallback_descriptions(self, product_data: Dict, image_analysis: Dict) -> Dict[str, Any]:
        """Fallback descriptions if Ollama fails"""
        product_name = image_analysis.get("product_name", "Product")
        category = image_analysis.get("category", "General")
        attributes = product_data.get("attributes", {})
        
        attr_text = ", ".join([f"{k}: {v}" for k, v in attributes.items() if k not in ["variant_stock"]])
        
        return {
            "english_title": f"{product_name} - {category} | ZOZI Oman",
            "english_description": f"High quality {product_name} available now at ZOZI Oman. {attr_text}. Order today with fast delivery across Oman.",
            "arabic_title": f"{product_name} - {category} | زوزي عمان",
            "arabic_description": f"{product_name} عالي الجودة متوفر الآن في زوزي عمان. {attr_text}. اطلب اليوم مع توصيل سريع لجميع أنحاء عمان.",
            "bullet_points_en": [f"✅ {k.title()}: {v}" for k, v in list(attributes.items())[:5] if k not in ["variant_stock"]],
            "bullet_points_ar": [f"✅ {k}: {v}" for k, v in list(attributes.items())[:5] if k not in ["variant_stock"]],
            "meta_title_en": f"{product_name} - Buy Online in Oman | ZOZI",
            "meta_description_en": f"Shop {product_name} at best price in Oman. {attr_text}. Fast delivery available.",
            "meta_title_ar": f"{product_name} - اشتري أونلاين في عمان | زوزي",
            "meta_description_ar": f"اشتري {product_name} بأفضل سعر في عمان. {attr_text}. توصيل سريع."
        }
    
    async def close(self):
        await self.client.aclose()


# ============================================
# DATA SAVER - CSV Export
# ============================================

class DataSaver:
    """Handles saving product data to CSV"""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.filepath = self.output_dir / "zozi_products.csv"
        
        self.fieldnames = [
            'product_id', 'sku', 'timestamp',
            'product_name', 'category', 'subcategory',
            'price_omr', 'stock_quantity', 'condition',
            'english_title', 'english_description',
            'arabic_title', 'arabic_description',
            'bullet_points_en', 'bullet_points_ar',
            'meta_title_en', 'meta_description_en',
            'meta_title_ar', 'meta_description_ar',
            'attributes', 'image_paths',
            'supplier_id', 'status'
        ]
    
    def generate_sku(self, product_name: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d")
        clean_name = re.sub(r'[^A-Za-z0-9]', '', product_name)[:8].upper()
        random_suffix = str(uuid.uuid4())[:4].upper()
        return f"ZOZI-{timestamp}-{clean_name}-{random_suffix}"
    
    def save_product(self, product_data: Dict, descriptions: Dict, image_analysis: Dict, image_paths: List[str], supplier_id: str = "supplier_001") -> str:
        product_id = str(uuid.uuid4())
        sku = self.generate_sku(product_data.get('english_title', 'Product'))
        
        row = {
            'product_id': product_id,
            'sku': sku,
            'timestamp': datetime.now().isoformat(),
            'product_name': image_analysis.get('product_name', ''),
            'category': image_analysis.get('category', ''),
            'subcategory': image_analysis.get('subcategory', ''),
            'price_omr': product_data.get('price_omr', 0.0),
            'stock_quantity': product_data.get('stock_quantity', 0),
            'condition': product_data.get('condition', 'new'),
            'english_title': descriptions.get('english_title', ''),
            'english_description': descriptions.get('english_description', ''),
            'arabic_title': descriptions.get('arabic_title', ''),
            'arabic_description': descriptions.get('arabic_description', ''),
            'bullet_points_en': json.dumps(descriptions.get('bullet_points_en', []), ensure_ascii=False),
            'bullet_points_ar': json.dumps(descriptions.get('bullet_points_ar', []), ensure_ascii=False),
            'meta_title_en': descriptions.get('meta_title_en', ''),
            'meta_description_en': descriptions.get('meta_description_en', ''),
            'meta_title_ar': descriptions.get('meta_title_ar', ''),
            'meta_description_ar': descriptions.get('meta_description_ar', ''),
            'attributes': json.dumps(product_data.get('attributes', {}), ensure_ascii=False),
            'image_paths': '|'.join(image_paths),
            'supplier_id': supplier_id,
            'status': 'draft'
        }
        
        file_exists = self.filepath.exists()
        with open(self.filepath, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
        
        logger.info(f"✅ Product saved to {self.filepath}")
        return product_id


# ============================================
# MAIN ORCHESTRATOR
# ============================================

class ProductUploadOrchestrator:
    def __init__(self):
        self.vision = ImageRecognitionService()
        self.interview = SmartInterviewService()
        self.descriptions = DescriptionGenerator()
        self.saver = DataSaver(Config.OUTPUT_DIR)
    
    async def upload_product(self, image_paths: List[str], supplier_id: str = "supplier_001") -> Dict[str, Any]:
        logger.info("=" * 70)
        logger.info("🚀 STARTING ZOZI PRODUCT UPLOAD")
        logger.info("=" * 70)
        
        logger.info("\n🔍 STEP 1: Analyzing product image...")
        image_analysis = await self.vision.analyze_image(image_paths[0])
        
        logger.info("\n💬 STEP 2: Conducting interview...")
        collected_data = await self.interview.conduct_interview(image_analysis)
        
        logger.info("\n✍️ STEP 3: Generating descriptions...")
        descriptions = await self.descriptions.generate_descriptions(collected_data, image_analysis)
        
        logger.info("\n" + "=" * 70)
        logger.info("📋 PRODUCT SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Name (EN): {descriptions.get('english_title')}")
        logger.info(f"Name (AR): {descriptions.get('arabic_title')}")
        logger.info(f"Category: {image_analysis.get('category')} > {image_analysis.get('subcategory')}")
        logger.info(f"Price: {collected_data.get('price_omr')} OMR")
        logger.info(f"Stock: {collected_data.get('stock_quantity')}")
        logger.info(f"Condition: {collected_data.get('condition')}")
        logger.info(f"Attributes: {json.dumps(collected_data.get('attributes', {}), indent=2, ensure_ascii=False)}")
        logger.info("=" * 70)
        
        logger.info("\n💾 STEP 4: Saving product data...")
        product_id = self.saver.save_product(collected_data, descriptions, image_analysis, image_paths, supplier_id)
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ PRODUCT UPLOAD COMPLETE!")
        logger.info("=" * 70)
        logger.info(f"Product ID: {product_id}")
        logger.info(f"Data saved to: {self.saver.filepath}")
        logger.info("=" * 70)
        
        return {
            'product_id': product_id,
            'product_data': collected_data,
            'image_analysis': image_analysis,
            'descriptions': descriptions
        }
    
    async def close(self):
        await self.vision.close()
        await self.descriptions.close()


# ============================================
# TEST FUNCTION
# ============================================

async def test_upload():
    try:
        await Config.validate()
    except Exception as e:
        print(f"\n❌ {e}")
        return
    
    print("\n" + "=" * 70)
    print("🧪 ZOZI PRODUCT UPLOAD SYSTEM - TEST")
    print("=" * 70)
    
    print("\n📸 Enter product image path:")
    path = input("Image path: ").strip().strip('"').strip("'")
    
    if not path or not os.path.exists(path):
        print(f"❌ File not found: {path}")
        return
    
    image_paths = [path]
    print(f"✅ Using image: {os.path.basename(path)}")
    
    supplier_id = input("\n👤 Supplier ID (press Enter for 'supplier_001'): ").strip() or "supplier_001"
    
    orchestrator = ProductUploadOrchestrator()
    
    try:
        result = await orchestrator.upload_product(image_paths, supplier_id)
        
        print("\n" + "=" * 70)
        print("🎉 TEST SUCCESSFUL!")
        print("=" * 70)
        print(f"✅ Product ID: {result['product_id']}")
        print(f"✅ Product: {result['descriptions'].get('english_title')}")
        print(f"✅ Category: {result['image_analysis'].get('category')}")
        print(f"✅ Price: {result['product_data'].get('price_omr')} OMR")
        print(f"✅ CSV: {orchestrator.saver.filepath}")
        print("=" * 70)
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}", exc_info=True)
        print(f"\n❌ Error: {str(e)}")
    finally:
        await orchestrator.close()


if __name__ == "__main__":
    import asyncio
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🚀 ZOZI Product Upload System                          ║
    ║                                                           ║
    ║   ✅ Automatic Image Detection (Moondream Vision)        ║
    ║   ✅ Smart Interview (With Color/Size Variant Matrix)    ║
    ║   ✅ Ollama AI (100% FREE - Runs on YOUR computer)       ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(test_upload())