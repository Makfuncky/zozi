# Combined Python Code

This file contains the combined source code from the project.

---

## 📄 upload_auto_04.py

```python
#!/usr/bin/env python3
"""
ZOZI Enterprise Product Upload Engine
======================================
Production-Ready AI Product Upload System with JSON Configuration

Architecture:
- zozi_variant_config.json: All variant definitions, categories, rules
- zozi_upload_engine.py: Business logic, AI services, database integration

Features:
✅ JSON-driven configuration (easy to maintain)
✅ Product-Type Intelligence (Liquid vs Solid vs Electronic vs Furniture)
✅ Mutual Exclusion Rules (No volume+weight, no size+dimensions)
✅ Database integration ready (PostgreSQL)
✅ Fallback to CSV for testing
"""

import os
import json
import csv
import uuid
import re
import base64
import itertools
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import httpx
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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
        """Load JSON configuration"""
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
        """Get all variant definitions"""
        return self.config.get("variants", {})
    
    def get_product_type_keywords(self) -> Dict[str, List[str]]:
        """Get product type keywords for classification"""
        return self.config.get("product_type_keywords", {})
    
    def get_category_fallbacks(self) -> Dict[str, List[str]]:
        """Get category fallback keywords"""
        return self.config.get("category_fallbacks", {})
    
    def get_ai_rules(self) -> Dict[str, Any]:
        """Get AI rules for variant selection"""
        return self.config.get("ai_rules", {})
    
    def get_variant_info(self, variant_key: str) -> Dict[str, Any]:
        """Get information about a specific variant"""
        return self.get_variants().get(variant_key, {})
    
    def get_mutually_exclusive(self, variant_key: str) -> List[str]:
        """Get mutually exclusive variants"""
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
        """Classify product into a type for intelligent variant selection"""
        text = f"{product_name} {category} {subcategory}".lower()
        keywords = self.config.get_product_type_keywords()
        
        # Check each product type
        for product_type, type_keywords in keywords.items():
            if any(kw in text for kw in type_keywords):
                return product_type
        
        # Fallback based on category
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
        """Get list of allowed variants for a category"""
        category_lower = category.lower().strip()
        subcategory_lower = subcategory.lower().strip()
        variants = self.config.get_variants()
        
        allowed = []
        
        # Strategy 1: Exact match
        for variant_key, variant_data in variants.items():
            if category_lower in variant_data["categories"] or \
               subcategory_lower in variant_data["categories"]:
                allowed.append(variant_key)
        
        # Strategy 2: Partial match
        if not allowed:
            for variant_key, variant_data in variants.items():
                for cat in variant_data["categories"]:
                    if category_lower in cat or cat in category_lower or \
                       subcategory_lower in cat or cat in subcategory_lower:
                        if variant_key not in allowed:
                            allowed.append(variant_key)
        
        # Strategy 3: Keyword-based fallback
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
        
        # Strategy 4: Ultimate fallback
        if not allowed:
            logger.warning("⚠️  No variants found. Using universal fallback.")
            allowed = ["color"]
        
        return allowed
    
    def get_variant_info(self, variant_key: str) -> Dict[str, Any]:
        """Get full information about a variant"""
        return self.config.get_variant_info(variant_key)
    
    def get_mutually_exclusive(self, variant_key: str) -> List[str]:
        """Get variants that are mutually exclusive with this one"""
        return self.config.get_mutually_exclusive(variant_key)


# ============================================================================
# SYSTEM CONFIGURATION
# ============================================================================

@dataclass
class SystemConfig:
    """System configuration for Ollama and Database"""
    
    # Ollama AI Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5"
    OLLAMA_VISION_MODEL: str = "moondream"
    
    # PostgreSQL Database Configuration
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "zozi_db")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    
    # System Settings
    USE_DATABASE: bool = False
    OUTPUT_DIR: str = "products_output"
    
    @classmethod
    async def validate(cls):
        """Validate Ollama is running"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{cls.OLLAMA_BASE_URL}/api/tags")
                if response.status_code != 200:
                    raise ConnectionError("Ollama is not responding")
                
                models = [m.get("name", "").split(":")[0] for m in response.json().get("models", [])]
                
                if cls.OLLAMA_VISION_MODEL not in models:
                    raise ValueError(f"Run: ollama pull {cls.OLLAMA_VISION_MODEL}")
                if cls.OLLAMA_MODEL not in models:
                    raise ValueError(f"Run: ollama pull {cls.OLLAMA_MODEL}")
                
                logger.info(f"✅ Ollama running: {cls.OLLAMA_MODEL} + {cls.OLLAMA_VISION_MODEL}")
        except httpx.ConnectError:
            raise ConnectionError("❌ Ollama is not running!")


# ============================================================================
# DATABASE CONNECTION
# ============================================================================

class DatabaseConnection:
    """PostgreSQL database connection manager"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.connection = None
    
    async def connect(self):
        """Connect to PostgreSQL database"""
        if not self.config.USE_DATABASE:
            logger.info("ℹ️  Database mode disabled - using JSON configuration")
            return
        
        try:
            import asyncpg
            self.connection = await asyncpg.connect(
                host=self.config.DB_HOST,
                port=self.config.DB_PORT,
                database=self.config.DB_NAME,
                user=self.config.DB_USER,
                password=self.config.DB_PASSWORD
            )
            logger.info(f"✅ Connected to PostgreSQL: {self.config.DB_NAME}")
        except ImportError:
            logger.error("❌ asyncpg not installed. Run: pip install asyncpg")
            raise
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    async def close(self):
        """Close database connection"""
        if self.connection:
            await self.connection.close()
            logger.info("🔌 Database connection closed")
    
    async def get_allowed_variants(self, category: str, subcategory: str, 
                                   master_db: MasterAttributeDatabase) -> List[str]:
        """Get allowed variants from database or fallback to JSON"""
        if not self.connection:
            return master_db.get_allowed_variants(category, subcategory)
        
        try:
            query = """
                SELECT a.attribute_key
                FROM attributes a
                JOIN category_attributes ca ON a.id = ca.attribute_id
                JOIN categories c ON ca.category_id = c.id
                WHERE c.name_en ILIKE $1 OR c.name_ar ILIKE $1
                OR c.name_en ILIKE $2 OR c.name_ar ILIKE $2
            """
            rows = await self.connection.fetch(query, f"%{category}%", f"%{subcategory}%")
            
            if rows:
                return [row['attribute_key'] for row in rows]
            else:
                return master_db.get_allowed_variants(category, subcategory)
                
        except Exception as e:
            logger.error(f"❌ Database query failed: {e}. Using JSON fallback.")
            return master_db.get_allowed_variants(category, subcategory)
    
    async def save_product(self, product_data: Dict, descriptions: Dict, 
                          image_analysis: Dict, image_paths: List[str], 
                          supplier_id: str) -> str:
        """Save product to database"""
        if not self.connection:
            logger.warning("⚠️  Database not connected - cannot save product")
            return ""
        
        try:
            product_id = str(uuid.uuid4())
            
            await self.connection.execute("""
                INSERT INTO products (
                    id, supplier_id, category_id, sku,
                    name_en, name_ar, slug_en,
                    price_omr, stock_quantity, condition, status,
                    attributes, ai_generated, published_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 'published', $11, true, NOW())
            """,
                product_id, supplier_id, None,
                f"ZOZI-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}",
                descriptions.get('english_title', ''),
                descriptions.get('arabic_title', ''),
                descriptions.get('english_title', '').lower().replace(' ', '-'),
                product_data.get('price_omr', 0.0),
                product_data.get('stock_quantity', 0),
                product_data.get('condition', 'new'),
                json.dumps(product_data.get('attributes', {}))
            )
            
            await self.connection.execute("""
                INSERT INTO product_descriptions (
                    id, product_id, language_code,
                    short_description, full_description, bullet_points,
                    ai_generated
                ) VALUES 
                ($1, $2, 'en', $3, $4, $5, true),
                ($6, $2, 'ar', $7, $8, $9, true)
            """,
                str(uuid.uuid4()), product_id,
                descriptions.get('english_description', '')[:500],
                descriptions.get('english_description', ''),
                json.dumps(descriptions.get('bullet_points_en', [])),
                str(uuid.uuid4()),
                descriptions.get('arabic_description', '')[:500],
                descriptions.get('arabic_description', ''),
                json.dumps(descriptions.get('bullet_points_ar', []))
            )
            
            logger.info(f"✅ Product saved to database: {product_id}")
            return product_id
            
        except Exception as e:
            logger.error(f"❌ Failed to save product: {e}")
            raise


# ============================================================================
# AI SERVICES
# ============================================================================

class AIService:
    """Handles all AI interactions with Ollama"""
    
    def __init__(self, config: SystemConfig, master_db: MasterAttributeDatabase):
        self.config = config
        self.master_db = master_db
        self.client = httpx.AsyncClient(
            base_url=f"{config.OLLAMA_BASE_URL}/v1",
            headers={"Content-Type": "application/json"},
            timeout=300.0
        )
    
    def encode_image(self, image_path: str) -> str:
        """Convert image to base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    async def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Step 1: AI Vision - Detect product from image"""
        logger.info(f"🔍 Analyzing image: {os.path.basename(image_path)}")
        image_base64 = self.encode_image(image_path)
        
        vision_prompt = """Look at this product carefully. Identify:
1. Exact product name (be specific, e.g., "Black T-Shirt", "Silver Necklace", "iPhone 13", "Olive Oil")
2. Brand (if visible)
3. Category (Electronics/Fashion/Home/Beauty/Jewelry/Automotive/Toys/Groceries/Sports/Books/Apparel)
4. Subcategory (specific type, e.g., T-Shirts, Necklaces, Smartphones, Olive Oil)
5. Color
6. Material (if visible)
7. Condition (new or used)

Be brief and accurate."""
        
        try:
            res = await self.client.post("/chat/completions", json={
                "model": self.config.OLLAMA_VISION_MODEL,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": vision_prompt},
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }}
                    ]
                }],
                "temperature": 0.3,
                "stream": False
            })
            
            raw_desc = res.json()["choices"][0]["message"]["content"]
            logger.info(f"👁️ Vision AI saw: {raw_desc.strip()}")
            
            format_prompt = f"""Extract details from this description into JSON:
"{raw_desc}"

CRITICAL: If a field is not detected or not applicable, use null (not "empty string" or "").

Return ONLY raw JSON (no markdown, no explanations):
{{
  "product_name": "Exact product name",
  "category": "Main category",
  "subcategory": "Specific type",
  "detected_attributes": {{
    "brand": "brand name or null",
    "color": "color or null",
    "material": "material or null",
    "model": "model or null"
  }},
  "condition": "new or used"
}}"""
            
            res2 = await self.client.post("/chat/completions", json={
                "model": self.config.OLLAMA_MODEL,
                "messages": [{"role": "user", "content": format_prompt}],
                "temperature": 0.1,
                "stream": False,
                "options": {"num_predict": 512}
            })
            
            content = res2.json()["choices"][0]["message"]["content"].strip()
            
            if "```" in content:
                content = re.sub(r'```[a-zA-Z]*\n?', '', content)
            
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                analysis = json.loads(json_match.group(), strict=False)
            else:
                analysis = json.loads(content, strict=False)
            
            if not analysis.get("product_name") or len(analysis["product_name"].strip()) < 3:
                analysis["product_name"] = " ".join(raw_desc.split()[:4]).capitalize()
            
            analysis.setdefault("category", "General")
            analysis.setdefault("subcategory", "General")
            analysis.setdefault("detected_attributes", {})
            analysis.setdefault("condition", "new")
            
            # Filter out null, None, empty strings, and "empty string" literal
            analysis["detected_attributes"] = {
                k: v for k, v in analysis["detected_attributes"].items() 
                if v and v not in [None, "", "null", "empty string", "N/A", "n/a"]
            }
            
            logger.info(f"✓ Detected: {analysis['product_name']} ({analysis['category']})")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Vision analysis failed: {e}")
            return await self._manual_fallback(image_path)
    
    async def match_variants_from_database(
        self,
        product_name: str,
        category: str,
        subcategory: str,
        detected_attributes: Dict,
        allowed_variants: List[str]
    ) -> Tuple[List[str], Dict[str, str]]:
        """Step 2: AI Matcher - Pick variants WITH PRODUCT TYPE INTELLIGENCE"""
        logger.info("🧠 AI matching variants with product-type intelligence...")
        
        # Classify product type
        product_type = self.master_db.classify_product_type(
            product_name, category, subcategory
        )
        logger.info(f"📦 Product type classified as: {product_type}")
        
        # Get AI rules from JSON
        ai_rules = self.config_loader.get_ai_rules() if hasattr(self, 'config_loader') else {}
        
        prompt = f"""You are an expert e-commerce product manager with deep product knowledge.

Product: "{product_name}"
Category: {category} > {subcategory}
Product Type: {product_type}
Already detected by vision: {json.dumps(detected_attributes)}

ALLOWED VARIANTS FROM DATABASE (you can ONLY choose from this list):
{json.dumps(allowed_variants)}

CRITICAL PRODUCT INTELLIGENCE RULES:

1. LIQUID PRODUCTS (oil, water, juice, milk, perfume, shampoo, lotion, beverages):
   - ONLY ask for "volume" (ml/L)
   - NEVER ask for "weight" (liquids are measured by volume, not weight)

2. SOLID FOOD (rice, flour, sugar, spices, coffee, tea, snacks):
   - ONLY ask for "weight" (g/kg)
   - NEVER ask for "volume" (solids are measured by weight, not volume)

3. FURNITURE (cupboard, cabinet, table, chair, sofa, bed):
   - ONLY ask for "dimensions" (actual measurements in cm)
   - NEVER ask for "size" (Small/Medium/Large doesn't make sense for furniture)

4. CLOTHING (shirt, t-shirt, pants, dress, jacket):
   - Ask for "size" (S/M/L/XL)
   - NEVER ask for "dimensions" (clothing uses standard sizes)

5. ELECTRONICS (phone, laptop, computer, tablet):
   - Ask for "storage", "ram", "model", "color"
   - NEVER ask for "weight" or "volume"

6. JEWELRY (necklace, ring, bracelet, watch):
   - Ask for "chain_length", "plating", "gemstone"
   - NEVER ask for "size" (except ring_size for rings)

7. MUTUAL EXCLUSION RULES:
   - If you select "volume", you CANNOT select "weight" (and vice versa)
   - If you select "size", you CANNOT select "dimensions" (and vice versa)
   - If you select "storage", you CANNOT select "weight" or "volume"

8. PRODUCT TYPE: {product_type}
   - For "liquid": ONLY volume
   - For "food_solid": ONLY weight
   - For "furniture": ONLY dimensions
   - For "clothing": ONLY size
   - For "electronic": storage, ram, model, color
   - For "jewelry": chain_length, plating, gemstone

TASK:
1. Choose which variants from the ALLOWED LIST are relevant for this specific product.
2. Identify which detected attributes need CONFIRMATION from supplier.
3. Apply the mutual exclusion rules above.

Return ONLY raw JSON:
{{
  "relevant_variants": ["variant1", "variant2"],
  "confirmations": {{
    "attribute_key": "detected_value"
  }},
  "reasoning": "Brief explanation of why you chose these variants"
}}"""
        
        try:
            res = await self.client.post("/chat/completions", json={
                "model": self.config.OLLAMA_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "stream": False,
                "options": {"num_predict": 768}
            })
            
            content = res.json()["choices"][0]["message"]["content"].strip()
            
            if "```" in content:
                content = re.sub(r'```[a-zA-Z]*\n?', '', content)
            
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                result = json.loads(json_match.group(), strict=False)
            else:
                result = json.loads(content, strict=False)
            
            variants = result.get("relevant_variants", [])
            confirmations = result.get("confirmations", {})
            reasoning = result.get("reasoning", "")
            
            # CRITICAL: Only keep variants that are in the database list
            variants = [v for v in variants if v in allowed_variants]
            
            # Remove duplicates between variants and confirmations
            variants = [v for v in variants if v not in confirmations]
            
            # Apply mutual exclusion rules
            variants = self._apply_mutual_exclusion(variants)
            
            # ENSURE: For apparel/clothing, always include size if available
            category_lower = category.lower()
            subcategory_lower = subcategory.lower()
            is_apparel = any(kw in category_lower or kw in subcategory_lower 
                           for kw in ["apparel", "clothing", "fashion", "shirt", 
                                     "t-shirt", "pants", "dress", "jacket"])
            
            if is_apparel and "size" in allowed_variants and "size" not in variants and "size" not in confirmations:
                logger.info("✓ Auto-adding 'size' for apparel product")
                variants.append("size")
            
            if reasoning:
                logger.info(f"💡 AI reasoning: {reasoning}")
            
            logger.info(f"✓ Relevant variants: {variants}")
            logger.info(f"✓ Confirmations needed: {list(confirmations.keys())}")
            
            return variants, confirmations
            
        except Exception as e:
            logger.error(f"❌ Variant matching failed: {e}")
            return ["color"] if "color" in allowed_variants else [], {}
    
    def _apply_mutual_exclusion(self, variants: List[str]) -> List[str]:
        """Apply mutual exclusion rules to prevent conflicting variants"""
        result = variants.copy()
        
        for variant in variants:
            if variant in result:
                exclusive_with = self.master_db.get_mutually_exclusive(variant)
                for exclusive_variant in exclusive_with:
                    if exclusive_variant in result:
                        logger.info(f"⚠️  Removing '{exclusive_variant}' (mutually exclusive with '{variant}')")
                        result.remove(exclusive_variant)
        
        return result
    
    async def generate_descriptions(self, product_data: Dict, image_analysis: Dict) -> Dict[str, Any]:
        """Step 3: Generate SEO descriptions"""
        logger.info("✍️ Generating descriptions...")
        
        product_name = image_analysis.get("product_name", "Product")
        category = image_analysis.get("category", "General")
        price = product_data.get('price_omr', 0)
        
        attr_list = []
        for k, v in product_data.get("attributes", {}).items():
            if k != "variant_stock":
                if isinstance(v, list):
                    attr_list.append(f"{k}: {', '.join(v)}")
                else:
                    attr_list.append(f"{k}: {v}")
        
        features_text = ", ".join(attr_list)
        
        prompt = f"""Create a professional e-commerce product listing.

Product: {product_name}
Category: {category}
Price: {price} OMR
Features: {features_text}

Generate compelling, SEO-optimized content in English and Arabic.

Return ONLY raw JSON:
{{
  "english_title": "Short SEO title (60-80 chars)",
  "english_description": "Description with ✅ bullet points",
  "arabic_title": "عنوان جذاب بالعربية",
  "arabic_description": "وصف بالعربية مع ✅ نقاط",
  "bullet_points_en": ["✅ Point 1", "✅ Point 2", "✅ Point 3"],
  "bullet_points_ar": ["✅ نقطة ١", "✅ نقطة ٢", "✅ نقطة ٣"],
  "meta_title_en": "SEO meta title",
  "meta_description_en": "SEO meta description",
  "meta_title_ar": "عنوان SEO",
  "meta_description_ar": "وصف SEO"
}}"""
        
        try:
            res = await self.client.post("/chat/completions", json={
                "model": self.config.OLLAMA_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "stream": False,
                "options": {"num_predict": 1024}
            })
            
            content = res.json()["choices"][0]["message"]["content"].strip()
            
            if "```" in content:
                content = re.sub(r'```[a-zA-Z]*\n?', '', content)
            
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                return json.loads(json_match.group(), strict=False)
            else:
                return json.loads(content, strict=False)
                
        except Exception as e:
            logger.error(f"❌ Description generation failed: {e}")
            return self._fallback_descriptions(product_data, image_analysis)
    
    async def _manual_fallback(self, image_path: str) -> Dict[str, Any]:
        """Fallback to manual input if vision fails"""
        print("\n📝 MANUAL INPUT (Vision AI failed)")
        return {
            "product_name": input("📦 Product name: ").strip(),
            "category": input("📂 Category: ").strip() or "General",
            "subcategory": input("📂 Subcategory: ").strip() or "General",
            "detected_attributes": {
                "brand": input("🏷️ Brand: ").strip(),
                "color": input("🎨 Color: ").strip()
            },
            "condition": input("📋 Condition (new/used) [new]: ").strip() or "new"
        }
    
    def _fallback_descriptions(self, product_data: Dict, image_analysis: Dict) -> Dict[str, Any]:
        """Fallback descriptions if AI fails"""
        name = image_analysis.get("product_name", "Product")
        cat = image_analysis.get("category", "General")
        return {
            "english_title": f"{name} - {cat} | ZOZI Oman",
            "english_description": f"High quality {name} available at ZOZI Oman.",
            "arabic_title": f"{name} - {cat} | زوزي عمان",
            "arabic_description": f"{name} عالي الجودة متوفر في زوزي عمان.",
            "bullet_points_en": ["✅ High Quality", "✅ Fast Delivery"],
            "bullet_points_ar": ["✅ جودة عالية", "✅ توصيل سريع"],
            "meta_title_en": f"{name} | ZOZI",
            "meta_description_en": f"Buy {name} online.",
            "meta_title_ar": f"{name} | زوزي",
            "meta_description_ar": f"اشتري {name} أونلاين."
        }
    
    async def close(self):
        """Close AI client"""
        await self.client.aclose()


# ============================================================================
# SMART INTERVIEW SERVICE
# ============================================================================

class SmartInterviewService:
    """Asks supplier questions based on JSON-configured variants"""
    
    def __init__(self, master_db: MasterAttributeDatabase):
        self.master_db = master_db
    
    async def conduct_interview(
        self,
        image_analysis: Dict,
        relevant_variants: List[str],
        confirmations: Dict[str, str]
    ) -> Dict[str, Any]:
        """Conduct interview with supplier"""
        logger.info("💬 Starting supplier interview...")
        
        category = image_analysis.get("category", "General")
        product_name = image_analysis.get("product_name", "Product")
        
        print("\n" + "=" * 70)
        print(f"💬 INTERVIEW FOR: {product_name} ({category})")
        print(f"🎯 Variants to collect: {relevant_variants}")
        print(f"🔍 Confirmations needed: {list(confirmations.keys())}")
        print("=" * 70)
        
        collected_data = {
            "condition": image_analysis.get("condition", "new")
        }
        attributes = image_analysis.get("detected_attributes", {}).copy()
        
        # 1. Price & Stock
        while True:
            try:
                price = float(input("\n💰 Price in OMR: ").strip())
                if price > 0:
                    collected_data["price_omr"] = price
                    break
                print("❌ Price must be > 0")
            except ValueError:
                print("❌ Invalid number")
        
        while True:
            try:
                stock_str = input("📦 Total Stock (or Enter to calculate from variants): ").strip()
                if not stock_str:
                    collected_data["stock_quantity"] = 0
                    break
                stock = int(stock_str)
                if stock >= 0:
                    collected_data["stock_quantity"] = stock
                    break
                print("❌ Stock cannot be negative")
            except ValueError:
                print("❌ Invalid number")
        
        # 2. Confirmations Phase
        if confirmations:
            print("\n🔍 Attribute Confirmations:")
            for key, detected_value in confirmations.items():
                variant_info = self.master_db.get_variant_info(key)
                key_display = variant_info.get("name", key).title()
                
                prompt_text = (
                    f"🧐 We detected {key_display}: {detected_value}. "
                    f"Is this correct, or do you have other options? "
                    f"(Press Enter to confirm, or type others comma-sep): "
                )
                user_input = input(prompt_text).strip()
                
                if not user_input:
                    attributes[key] = [detected_value]
                else:
                    typed_options = [v.strip() for v in user_input.split(',')]
                    if detected_value not in typed_options:
                        typed_options.insert(0, detected_value)
                    attributes[key] = typed_options
        
        # 3. Dynamic Variant Questions
        if relevant_variants:
            print("\n🎨 Product Variants:")
            for variant_key in relevant_variants:
                variant_info = self.master_db.get_variant_info(variant_key)
                if variant_info:
                    prompt = variant_info.get("prompt", f"Enter {variant_key}: ")
                    user_input = input(f"{prompt}: ").strip()
                    
                    if user_input:
                        attributes[variant_key] = [v.strip() for v in user_input.split(',')]
        
        # 4. Variant Stock Matrix
        all_variant_keys = list(confirmations.keys()) + relevant_variants
        variant_types = [
            v for v in all_variant_keys
            if v in attributes and isinstance(attributes[v], list)
        ]
        
        if len(variant_types) >= 2:
            print("\n📦 Stock Distribution:")
            print("1. Same stock for all variants")
            print("2. Different stock for each combination (Matrix)")
            
            if input("Enter 1 or 2 [1]: ").strip() == "2":
                variant_stock = {}
                total = 0
                
                combinations = list(itertools.product(
                    *[attributes[v] for v in variant_types]
                ))
                
                for combo in combinations:
                    combo_name = " - ".join(combo)
                    while True:
                        qty = input(f"  🔹 {combo_name}: ").strip()
                        if not qty:
                            variant_stock[combo_name] = 0
                            break
                        if qty.isdigit():
                            variant_stock[combo_name] = int(qty)
                            total += int(qty)
                            break
                        print("    ❌ Enter a number or press Enter for 0.")
                
                collected_data["stock_quantity"] = total
                attributes["variant_stock"] = variant_stock
                logger.info(f"✓ Total stock from matrix: {total}")
        
        elif len(variant_types) == 1:
            var_key = variant_types[0]
            print(f"\n📦 Stock per {var_key.replace('_', ' ').title()}:")
            variant_stock = {}
            total = 0
            
            for item in attributes[var_key]:
                while True:
                    qty = input(f"  🔹 {item}: ").strip()
                    if not qty:
                        variant_stock[item] = 0
                        break
                    if qty.isdigit():
                        variant_stock[item] = int(qty)
                        total += int(qty)
                        break
                    print("    ❌ Enter a number or press Enter for 0.")
            
            collected_data["stock_quantity"] = total
            attributes["variant_stock"] = variant_stock
            logger.info(f"✓ Total stock from {var_key}: {total}")
        
        collected_data["attributes"] = attributes
        logger.info("✓ Interview complete")
        return collected_data


# ============================================================================
# CSV EXPORT
# ============================================================================

class CSVExporter:
    """Export product data to CSV"""
    
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
    
    def save_product(
        self,
        product_data: Dict,
        descriptions: Dict,
        image_analysis: Dict,
        image_paths: List[str],
        supplier_id: str
    ) -> str:
        """Save product to CSV"""
        product_id = str(uuid.uuid4())
        sku = (
            f"ZOZI-{datetime.now().strftime('%Y%m%d')}-"
            f"{re.sub(r'[^A-Za-z0-9]', '', product_data.get('english_title', 'P'))[:8].upper()}-"
            f"{str(uuid.uuid4())[:4].upper()}"
        )
        
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
            'bullet_points_en': json.dumps(
                descriptions.get('bullet_points_en', []), ensure_ascii=False
            ),
            'bullet_points_ar': json.dumps(
                descriptions.get('bullet_points_ar', []), ensure_ascii=False
            ),
            'meta_title_en': descriptions.get('meta_title_en', ''),
            'meta_description_en': descriptions.get('meta_description_en', ''),
            'meta_title_ar': descriptions.get('meta_title_ar', ''),
            'meta_description_ar': descriptions.get('meta_description_ar', ''),
            'attributes': json.dumps(
                product_data.get('attributes', {}), ensure_ascii=False
            ),
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
        
        logger.info(f"✅ Saved to CSV: {self.filepath}")
        return product_id


# ============================================================================
# MAIN ORCHESTRATOR
# ============================================================================

class ProductUploadOrchestrator:
    """Main orchestrator for the entire upload process"""
    
    def __init__(self, config: SystemConfig, config_loader: ConfigLoader):
        self.config = config
        self.config_loader = config_loader
        self.master_db = MasterAttributeDatabase(config_loader)
        self.ai = AIService(config, self.master_db)
        self.db = DatabaseConnection(config)
        self.interview = SmartInterviewService(self.master_db)
        self.csv_exporter = CSVExporter(config.OUTPUT_DIR)
    
    async def initialize(self):
        """Initialize connections"""
        if self.config.USE_DATABASE:
            await self.db.connect()
    
    async def upload_product(
        self,
        image_paths: List[str],
        supplier_id: str
    ) -> Dict[str, Any]:
        """Complete product upload workflow"""
        logger.info("=" * 70)
        logger.info("🚀 STARTING ZOZI PRODUCT UPLOAD - JSON-DRIVEN ENGINE")
        logger.info("=" * 70)
        
        # Step 1: AI Vision
        logger.info("\n🔍 STEP 1: Analyzing image...")
        image_analysis = await self.ai.analyze_image(image_paths[0])
        
        # Step 2: JSON Config - Get allowed variants
        logger.info("\n📊 STEP 2: Fetching allowed variants from JSON configuration...")
        allowed_variants = await self.db.get_allowed_variants(
            image_analysis.get("category"),
            image_analysis.get("subcategory"),
            self.master_db
        )
        logger.info(f"✓ Allowed variants: {len(allowed_variants)} options - {allowed_variants}")
        
        # Step 3: AI Matcher with Product Intelligence
        logger.info("\n🎯 STEP 3: AI matching variants with product intelligence...")
        relevant_variants, confirmations = await self.ai.match_variants_from_database(
            image_analysis.get("product_name"),
            image_analysis.get("category"),
            image_analysis.get("subcategory"),
            image_analysis.get("detected_attributes", {}),
            allowed_variants
        )
        
        # Step 4: Interview
        logger.info("\n💬 STEP 4: Supplier interview...")
        collected_data = await self.interview.conduct_interview(
            image_analysis,
            relevant_variants,
            confirmations
        )
        
        # Step 5: Descriptions
        logger.info("\n✍️ STEP 5: Generating descriptions...")
        descriptions = await self.ai.generate_descriptions(
            collected_data,
            image_analysis
        )
        
        # Step 6: Save
        logger.info("\n💾 STEP 6: Saving product...")
        
        if self.config.USE_DATABASE:
            product_id = await self.db.save_product(
                collected_data,
                descriptions,
                image_analysis,
                image_paths,
                supplier_id
            )
        else:
            product_id = self.csv_exporter.save_product(
                collected_data,
                descriptions,
                image_analysis,
                image_paths,
                supplier_id
            )
        
        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("📋 PRODUCT SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Name (EN): {descriptions.get('english_title')}")
        logger.info(f"Name (AR): {descriptions.get('arabic_title')}")
        logger.info(f"Category: {image_analysis.get('category')} > {image_analysis.get('subcategory')}")
        logger.info(f"Price: {collected_data.get('price_omr')} OMR")
        logger.info(f"Stock: {collected_data.get('stock_quantity')}")
        logger.info(f"Variants: {relevant_variants}")
        logger.info(f"Attributes: {json.dumps(collected_data.get('attributes', {}), indent=2, ensure_ascii=False)}")
        logger.info("=" * 70)
        
        logger.info(f"\n✅ COMPLETE! Product ID: {product_id}")
        
        return {
            'product_id': product_id,
            'product_data': collected_data,
            'image_analysis': image_analysis,
            'descriptions': descriptions,
            'relevant_variants': relevant_variants
        }
    
    async def close(self):
        """Close all connections"""
        await self.ai.close()
        await self.db.close()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """Main test function"""
    
    try:
        await SystemConfig.validate()
    except Exception as e:
        print(f"\n❌ {e}")
        return
    
    # Load JSON configuration
    try:
        config_loader = ConfigLoader("zozi_variant_config.json")
    except Exception as e:
        print(f"\n❌ Failed to load configuration: {e}")
        return
    
    print("\n" + "=" * 70)
    print("🧪 ZOZI ENTERPRISE PRODUCT UPLOAD SYSTEM - JSON-DRIVEN")
    print("=" * 70)
    
    path = input("\n📸 Enter product image path: ").strip().strip('"').strip("'")
    
    if not path or not os.path.exists(path):
        print(f"❌ File not found: {path}")
        return
    
    supplier_id = input("\n👤 Supplier ID [supplier_001]: ").strip() or "supplier_001"
    
    config = SystemConfig()
    orchestrator = ProductUploadOrchestrator(config, config_loader)
    
    try:
        await orchestrator.initialize()
        result = await orchestrator.upload_product([path], supplier_id)
        
        print("\n" + "=" * 70)
        print("🎉 SUCCESS!")
        print("=" * 70)
        print(f"✅ Product ID: {result['product_id']}")
        print(f"✅ Product: {result['descriptions'].get('english_title')}")
        print(f"✅ Category: {result['image_analysis'].get('category')}")
        print(f"✅ Price: {result['product_data'].get('price_omr')} OMR")
        print(f"✅ Variants: {result['relevant_variants']}")
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
    ║   🚀 ZOZI Enterprise Product Upload Engine                ║
    ║   📊 JSON-DRIVEN CONFIGURATION                            ║
    ║                                                           ║
    ║   ✅ Configuration: zozi_variant_config.json             ║
    ║   ✅ Business Logic: zozi_upload_engine.py               ║
    ║   ✅ Product-Type Intelligence                           ║
    ║   ✅ Mutual Exclusion Rules                              ║
    ║   ✅ Database Ready (PostgreSQL)                         ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(main())
```

---

## 📄 zozi_variant_config.json

```python
{
  "version": "1.0.0",
  "description": "ZOZI E-Commerce Variant Configuration - All product variants, categories, and rules",
  
  "variants": {
    "color": {
      "name": "Color",
      "name_ar": "اللون",
      "prompt": "🎨 Available colors (comma-sep, e.g., Black, White, Red, Blue)",
      "type": "text",
      "categories": [
        "fashion", "apparel", "clothing", "shoes", "accessories",
        "home", "electronics", "toys", "automotive", "jewelry",
        "bags", "watches", "sunglasses", "hats", "scarves",
        "t-shirts", "shirts", "pants", "dresses", "skirts",
        "jackets", "coats", "sweaters", "hoodies", "furniture",
        "appliances", "kitchen", "refrigerators"
      ],
      "product_types": ["clothing", "electronic", "furniture", "appliance", "accessory", "jewelry", "toy", "automotive"],
      "mutually_exclusive_with": []
    },
    
    "size": {
      "name": "Size",
      "name_ar": "المقاس",
      "prompt": "📏 Available sizes (comma-sep, e.g., S, M, L, XL, XXL or 40, 41, 42, 43)",
      "type": "text",
      "categories": [
        "fashion", "apparel", "clothing", "shoes", "accessories",
        "t-shirts", "shirts", "pants", "dresses", "skirts",
        "jackets", "coats", "sweaters", "hoodies", "jeans",
        "shorts", "socks", "underwear", "lingerie", "swimwear",
        "sportswear", "activewear", "kids", "baby", "children"
      ],
      "product_types": ["clothing", "shoes"],
      "mutually_exclusive_with": ["dimensions"]
    },
    
    "material": {
      "name": "Material",
      "name_ar": "المادة",
      "prompt": "🧵 Available materials (comma-sep, e.g., Cotton, Polyester, Leather, Silk, Wool, Denim, Stainless Steel)",
      "type": "text",
      "categories": [
        "fashion", "apparel", "clothing", "shoes", "accessories",
        "home", "furniture", "jewelry", "bags", "t-shirts",
        "shirts", "pants", "dresses", "jackets", "coats",
        "sweaters", "hoodies", "jeans", "socks", "underwear",
        "kitchen", "appliances"
      ],
      "product_types": ["clothing", "furniture", "jewelry", "appliance"],
      "mutually_exclusive_with": []
    },
    
    "pattern": {
      "name": "Pattern",
      "name_ar": "النقشة",
      "prompt": "🎨 Available patterns (comma-sep, e.g., Solid, Striped, Floral, Plaid, Checkered, Graphic)",
      "type": "text",
      "categories": [
        "fashion", "apparel", "clothing", "home", "t-shirts",
        "shirts", "pants", "dresses", "skirts", "jackets",
        "coats", "sweaters", "hoodies", "jeans"
      ],
      "product_types": ["clothing"],
      "mutually_exclusive_with": []
    },
    
    "gender": {
      "name": "Gender",
      "name_ar": "الجنس",
      "prompt": "👤 Target gender (comma-sep, e.g., Men, Women, Unisex, Boys, Girls)",
      "type": "text",
      "categories": [
        "fashion", "apparel", "clothing", "shoes", "accessories",
        "toys", "bags", "watches", "sunglasses", "hats",
        "t-shirts", "shirts", "pants", "dresses", "kids",
        "baby", "children", "sportswear", "activewear"
      ],
      "product_types": ["clothing", "shoes", "accessory"],
      "mutually_exclusive_with": []
    },
    
    "sleeve_length": {
      "name": "Sleeve Length",
      "name_ar": "طول الأكمام",
      "prompt": "👕 Sleeve length options (comma-sep, e.g., Short, Long, Sleeveless, Half, Three-Quarter)",
      "type": "text",
      "categories": [
        "fashion", "apparel", "clothing", "t-shirts", "shirts",
        "dresses", "jackets", "coats", "sweaters", "hoodies",
        "blouses", "tops"
      ],
      "product_types": ["clothing"],
      "mutually_exclusive_with": []
    },
    
    "neckline": {
      "name": "Neckline",
      "name_ar": "خط العنق",
      "prompt": "👔 Neckline options (comma-sep, e.g., Crew Neck, V-Neck, Polo, Round, Square, Boat)",
      "type": "text",
      "categories": [
        "fashion", "apparel", "clothing", "t-shirts", "shirts",
        "dresses", "sweaters", "hoodies", "blouses", "tops"
      ],
      "product_types": ["clothing"],
      "mutually_exclusive_with": []
    },
    
    "fit": {
      "name": "Fit",
      "name_ar": "المقاس",
      "prompt": "👕 Fit options (comma-sep, e.g., Slim, Regular, Relaxed, Oversized, Skinny)",
      "type": "text",
      "categories": [
        "fashion", "apparel", "clothing", "t-shirts", "shirts",
        "pants", "jeans", "dresses", "jackets", "coats"
      ],
      "product_types": ["clothing"],
      "mutually_exclusive_with": []
    },
    
    "storage": {
      "name": "Storage",
      "name_ar": "التخزين",
      "prompt": "💾 Storage options (comma-sep, e.g., 64GB, 128GB, 256GB, 512GB, 1TB, 2TB)",
      "type": "text",
      "categories": [
        "electronics", "phones", "laptops", "tablets", "computers",
        "smartphones", "mobile", "cameras", "gaming", "consoles",
        "hard drives", "ssd", "usb", "memory cards"
      ],
      "product_types": ["electronic"],
      "mutually_exclusive_with": ["weight", "volume"]
    },
    
    "ram": {
      "name": "RAM",
      "name_ar": "الذاكرة العشوائية",
      "prompt": "💻 RAM options (comma-sep, e.g., 4GB, 8GB, 16GB, 32GB, 64GB)",
      "type": "text",
      "categories": [
        "electronics", "laptops", "desktops", "computers", "tablets"
      ],
      "product_types": ["electronic"],
      "mutually_exclusive_with": ["weight", "volume"]
    },
    
    "model": {
      "name": "Model/Version",
      "name_ar": "الموديل",
      "prompt": "📦 Available models/versions (comma-sep, e.g., 2023, 2024, Pro, Plus, Max, 13 Pro Max)",
      "type": "text",
      "categories": [
        "electronics", "phones", "laptops", "automotive",
        "smartphones", "mobile", "tablets", "cameras",
        "gaming", "consoles", "tvs", "monitors"
      ],
      "product_types": ["electronic", "automotive"],
      "mutually_exclusive_with": []
    },
    
    "screen_size": {
      "name": "Screen Size",
      "name_ar": "حجم الشاشة",
      "prompt": "📱 Screen sizes in inches (comma-sep, e.g., 5.5, 6.1, 6.7, 13, 15, 17, 24, 27, 32)",
      "type": "text",
      "categories": [
        "electronics", "laptops", "monitors", "phones",
        "smartphones", "mobile", "tablets", "tvs", "displays"
      ],
      "product_types": ["electronic"],
      "mutually_exclusive_with": []
    },
    
    "connectivity": {
      "name": "Connectivity",
      "name_ar": "الاتصال",
      "prompt": "📡 Connectivity options (comma-sep, e.g., WiFi, Bluetooth, 4G, 5G, NFC, USB-C)",
      "type": "text",
      "categories": [
        "electronics", "phones", "laptops", "smartphones",
        "mobile", "tablets", "wearables", "smartwatches"
      ],
      "product_types": ["electronic"],
      "mutually_exclusive_with": []
    },
    
    "processor": {
      "name": "Processor",
      "name_ar": "المعالج",
      "prompt": "⚙️ Processor options (comma-sep, e.g., Intel i5, Intel i7, AMD Ryzen 5, M1, M2)",
      "type": "text",
      "categories": [
        "electronics", "laptops", "desktops", "computers", "tablets"
      ],
      "product_types": ["electronic"],
      "mutually_exclusive_with": []
    },
    
    "chain_length": {
      "name": "Chain Length",
      "name_ar": "طول السلسلة",
      "prompt": "📏 Chain lengths in inches (comma-sep, e.g., 16, 18, 20, 22, 24, 30)",
      "type": "text",
      "categories": [
        "jewelry", "necklaces", "pendants", "chains", "accessories"
      ],
      "product_types": ["jewelry"],
      "mutually_exclusive_with": []
    },
    
    "plating": {
      "name": "Plating",
      "name_ar": "الطلاء",
      "prompt": "✨ Plating options (comma-sep, e.g., Gold, Silver, Rose Gold, Platinum, Rhodium)",
      "type": "text",
      "categories": [
        "jewelry", "watches", "rings", "necklaces", "bracelets",
        "earrings", "pendants", "accessories"
      ],
      "product_types": ["jewelry"],
      "mutually_exclusive_with": []
    },
    
    "watch_strap": {
      "name": "Watch Strap",
      "name_ar": "سوار الساعة",
      "prompt": "⌚ Watch strap types (comma-sep, e.g., Leather, Metal, Silicone, Nylon, Rubber, Ceramic)",
      "type": "text",
      "categories": [
        "watches", "jewelry", "smartwatches", "wearables", "accessories"
      ],
      "product_types": ["jewelry", "electronic"],
      "mutually_exclusive_with": []
    },
    
    "gemstone": {
      "name": "Gemstone",
      "name_ar": "الحجر الكريم",
      "prompt": "💎 Gemstone options (comma-sep, e.g., Diamond, Ruby, Emerald, Sapphire, Pearl, Opal)",
      "type": "text",
      "categories": [
        "jewelry", "rings", "necklaces", "bracelets", "earrings",
        "pendants", "accessories"
      ],
      "product_types": ["jewelry"],
      "mutually_exclusive_with": []
    },
    
    "ring_size": {
      "name": "Ring Size",
      "name_ar": "مقاس الخاتم",
      "prompt": "💍 Ring sizes (comma-sep, e.g., 5, 6, 7, 8, 9, 10, 11, 12)",
      "type": "text",
      "categories": [
        "jewelry", "rings", "accessories"
      ],
      "product_types": ["jewelry"],
      "mutually_exclusive_with": []
    },
    
    "bracelet_size": {
      "name": "Bracelet Size",
      "name_ar": "مقاس السوار",
      "prompt": "📿 Bracelet sizes (comma-sep, e.g., Small, Medium, Large, 6.5 inch, 7 inch, 7.5 inch)",
      "type": "text",
      "categories": [
        "jewelry", "bracelets", "watches", "accessories"
      ],
      "product_types": ["jewelry"],
      "mutually_exclusive_with": []
    },
    
    "scent": {
      "name": "Scent/Fragrance",
      "name_ar": "العطر",
      "prompt": "🌸 Available scents (comma-sep, e.g., Rose, Oud, Vanilla, Jasmine, Lavender, Citrus)",
      "type": "text",
      "categories": [
        "beauty", "perfumes", "home", "candles", "air fresheners",
        "cosmetics", "skincare", "haircare"
      ],
      "product_types": ["beauty"],
      "mutually_exclusive_with": []
    },
    
    "flavor": {
      "name": "Flavor",
      "name_ar": "النكهة",
      "prompt": "🍓 Available flavors (comma-sep, e.g., Chocolate, Strawberry, Vanilla, Mint, Coffee, Original)",
      "type": "text",
      "categories": [
        "groceries", "food", "beverages", "snacks", "candy",
        "chocolate", "ice cream", "supplements"
      ],
      "product_types": ["food_solid"],
      "mutually_exclusive_with": []
    },
    
    "weight": {
      "name": "Weight",
      "name_ar": "الوزن",
      "prompt": "⚖️ Weight options (comma-sep, e.g., 50g, 100g, 250g, 500g, 1kg, 2kg)",
      "type": "text",
      "categories": [
        "groceries", "food", "beauty", "supplements", "snacks",
        "rice", "flour", "sugar", "spices"
      ],
      "product_types": ["food_solid"],
      "mutually_exclusive_with": ["volume"]
    },
    
    "volume": {
      "name": "Volume",
      "name_ar": "الحجم",
      "prompt": "🧴 Volume options (comma-sep, e.g., 30ml, 50ml, 100ml, 250ml, 500ml, 1L, 2L)",
      "type": "text",
      "categories": [
        "beauty", "groceries", "beverages", "home", "cosmetics",
        "skincare", "haircare", "shampoo", "lotion", "perfume",
        "water", "juice", "milk", "oil"
      ],
      "product_types": ["liquid"],
      "mutually_exclusive_with": ["weight"]
    },
    
    "skin_type": {
      "name": "Skin Type",
      "name_ar": "نوع البشرة",
      "prompt": "🧴 Skin type options (comma-sep, e.g., All Skin Types, Oily, Dry, Sensitive, Combination)",
      "type": "text",
      "categories": [
        "beauty", "cosmetics", "skincare", "haircare"
      ],
      "product_types": ["beauty"],
      "mutually_exclusive_with": []
    },
    
    "capacity": {
      "name": "Capacity",
      "name_ar": "السعة",
      "prompt": "📦 Capacity options (comma-sep, e.g., 50L, 100L, 200L, 300L, 500L, 1000L)",
      "type": "text",
      "categories": [
        "home", "appliances", "refrigerators", "washing machines",
        "ovens", "microwaves", "dishwashers", "air conditioners"
      ],
      "product_types": ["appliance"],
      "mutually_exclusive_with": []
    },
    
    "voltage": {
      "name": "Voltage",
      "name_ar": "الجهد",
      "prompt": "⚡ Voltage options (comma-sep, e.g., 110V, 220V, 240V, 380V)",
      "type": "text",
      "categories": [
        "electronics", "appliances", "home", "tools", "machinery"
      ],
      "product_types": ["appliance", "electronic"],
      "mutually_exclusive_with": []
    },
    
    "wattage": {
      "name": "Wattage",
      "name_ar": "القدرة",
      "prompt": "💡 Wattage options (comma-sep, e.g., 40W, 60W, 100W, 150W, 500W, 1000W, 2000W)",
      "type": "text",
      "categories": [
        "electronics", "appliances", "lighting", "home", "tools"
      ],
      "product_types": ["appliance", "electronic"],
      "mutually_exclusive_with": []
    },
    
    "dimensions": {
      "name": "Dimensions",
      "name_ar": "الأبعاد",
      "prompt": "📐 Dimensions in cm (comma-sep, e.g., 180cm x 60cm x 40cm, 200cm x 80cm x 50cm, 120cm x 50cm x 30cm)",
      "type": "text",
      "categories": [
        "home", "furniture", "appliances", "decor", "rugs",
        "curtains", "cushions", "tables", "chairs", "sofas", "beds",
        "kitchen", "cupboards", "cabinets"
      ],
      "product_types": ["furniture", "appliance"],
      "mutually_exclusive_with": ["size"]
    },
    
    "color_temperature": {
      "name": "Color Temperature",
      "name_ar": "درجة حرارة اللون",
      "prompt": "💡 Color temperature options (comma-sep, e.g., Warm White, Cool White, Daylight, RGB)",
      "type": "text",
      "categories": [
        "lighting", "home", "electronics", "led", "bulbs"
      ],
      "product_types": ["appliance"],
      "mutually_exclusive_with": []
    },
    
    "age_group": {
      "name": "Age Group",
      "name_ar": "الفئة العمرية",
      "prompt": "👶 Age groups (comma-sep, e.g., 0-2 Years, 3-5 Years, 6-8 Years, 9-12 Years, Teens)",
      "type": "text",
      "categories": [
        "toys", "kids", "baby", "children", "games", "puzzles",
        "educational", "outdoor", "sports"
      ],
      "product_types": ["toy"],
      "mutually_exclusive_with": []
    },
    
    "toy_type": {
      "name": "Toy Type",
      "name_ar": "نوع اللعبة",
      "prompt": "🧸 Toy type options (comma-sep, e.g., Action Figures, Dolls, Building Blocks, Vehicles, Puzzles)",
      "type": "text",
      "categories": [
        "toys", "kids", "baby", "children", "games"
      ],
      "product_types": ["toy"],
      "mutually_exclusive_with": []
    },
    
    "car_fitment": {
      "name": "Car Fitment",
      "name_ar": "توافق السيارة",
      "prompt": "🚗 Car models this fits (comma-sep, e.g., Toyota Camry 2018-2022, Nissan Altima, Honda Accord)",
      "type": "text",
      "categories": [
        "automotive", "car_parts", "accessories", "tires",
        "batteries", "oil", "filters", "brakes", "suspension"
      ],
      "product_types": ["automotive"],
      "mutually_exclusive_with": []
    },
    
    "vehicle_type": {
      "name": "Vehicle Type",
      "name_ar": "نوع المركبة",
      "prompt": "🏍️ Vehicle types (comma-sep, e.g., Car, SUV, Truck, Motorcycle, Bicycle, Van)",
      "type": "text",
      "categories": [
        "automotive", "accessories", "tires", "parts"
      ],
      "product_types": ["automotive"],
      "mutually_exclusive_with": []
    },
    
    "year": {
      "name": "Year",
      "name_ar": "السنة",
      "prompt": "📅 Year options (comma-sep, e.g., 2020, 2021, 2022, 2023, 2024)",
      "type": "text",
      "categories": [
        "automotive", "electronics", "appliances", "cars",
        "motorcycles", "bicycles"
      ],
      "product_types": ["automotive", "electronic", "appliance"],
      "mutually_exclusive_with": []
    },
    
    "sport_type": {
      "name": "Sport Type",
      "name_ar": "نوع الرياضة",
      "prompt": "⚽ Sport type options (comma-sep, e.g., Football, Basketball, Tennis, Swimming, Running, Cycling)",
      "type": "text",
      "categories": [
        "sports", "outdoor", "fitness", "gym", "equipment"
      ],
      "product_types": ["sport"],
      "mutually_exclusive_with": []
    },
    
    "language": {
      "name": "Language",
      "name_ar": "اللغة",
      "prompt": "🌐 Language options (comma-sep, e.g., English, Arabic, French, Spanish, Chinese)",
      "type": "text",
      "categories": [
        "books", "stationery", "educational", "magazines"
      ],
      "product_types": ["book"],
      "mutually_exclusive_with": []
    },
    
    "binding": {
      "name": "Binding",
      "name_ar": "الغلاف",
      "prompt": "📚 Binding options (comma-sep, e.g., Hardcover, Paperback, Spiral, eBook)",
      "type": "text",
      "categories": [
        "books", "stationery", "educational"
      ],
      "product_types": ["book"],
      "mutually_exclusive_with": []
    }
  },
  
  "product_type_keywords": {
    "liquid": ["oil", "water", "juice", "milk", "perfume", "shampoo", "lotion", "beverage", "drink", "syrup", "honey", "vinegar", "sauce"],
    "food_solid": ["rice", "flour", "sugar", "spice", "salt", "coffee", "tea", "chocolate", "candy", "snack", "nut", "grain", "cereal"],
    "clothing": ["shirt", "t-shirt", "pants", "dress", "jacket", "coat", "sweater", "hoodie", "jeans", "shorts", "socks", "underwear", "skirt", "blouse", "top"],
    "shoes": ["shoe", "sneaker", "boot", "sandal", "slipper", "footwear"],
    "electronic": ["phone", "laptop", "computer", "tablet", "tv", "monitor", "camera", "headphone", "speaker", "charger", "cable", "iphone", "samsung", "macbook"],
    "furniture": ["cupboard", "cabinet", "table", "chair", "sofa", "bed", "desk", "shelf", "bookcase", "wardrobe", "dresser"],
    "appliance": ["refrigerator", "fridge", "oven", "microwave", "washing machine", "dishwasher", "air conditioner", "blender", "toaster", "kettle"],
    "jewelry": ["necklace", "ring", "bracelet", "earring", "pendant", "chain", "watch", "jewelry", "jewellery"],
    "toy": ["toy", "game", "puzzle", "doll", "figure", "lego", "playset"],
    "book": ["book", "magazine", "novel", "textbook", "notebook"],
    "automotive": ["car", "tire", "battery", "oil filter", "brake", "suspension", "engine", "motor"],
    "beauty": ["cosmetic", "makeup", "skincare", "lipstick", "foundation", "mascara", "eyeliner"],
    "sport": ["football", "basketball", "tennis", "gym", "fitness", "yoga", "running"]
  },
  
  "category_fallbacks": {
    "apparel_keywords": ["apparel", "clothing", "fashion", "shirt", "t-shirt", "pants", "dress", "jacket", "coat", "sweater", "hoodie"],
    "electronics_keywords": ["electronics", "phone", "laptop", "computer", "tablet", "camera", "tv", "monitor"],
    "jewelry_keywords": ["jewelry", "jewellery", "ring", "necklace", "bracelet", "earring", "watch"],
    "home_keywords": ["home", "furniture", "decor", "appliance", "kitchen", "bedroom", "living"],
    "beauty_keywords": ["beauty", "cosmetic", "skincare", "makeup", "perfume", "haircare"],
    "groceries_keywords": ["groceries", "food", "beverage", "snack", "drink", "rice", "oil", "spice"],
    "toys_keywords": ["toy", "game", "kids", "baby", "children"],
    "automotive_keywords": ["automotive", "car", "vehicle", "motorcycle", "bicycle", "tire", "part"]
  },
  
  "ai_rules": {
    "liquid_rules": {
      "description": "For liquid products (oil, water, juice, milk, perfume, shampoo, lotion, beverages)",
      "include": ["volume"],
      "exclude": ["weight"],
      "reason": "Liquids are measured by volume (ml/L), not weight"
    },
    "food_solid_rules": {
      "description": "For solid food products (rice, flour, sugar, spices, coffee, tea, snacks)",
      "include": ["weight"],
      "exclude": ["volume"],
      "reason": "Solid foods are measured by weight (g/kg), not volume"
    },
    "furniture_rules": {
      "description": "For furniture (cupboard, cabinet, table, chair, sofa, bed)",
      "include": ["dimensions"],
      "exclude": ["size"],
      "reason": "Furniture uses actual measurements in cm, not S/M/L sizes"
    },
    "clothing_rules": {
      "description": "For clothing (shirt, t-shirt, pants, dress, jacket)",
      "include": ["size"],
      "exclude": ["dimensions"],
      "reason": "Clothing uses standard sizes (S/M/L/XL), not dimensions"
    },
    "electronic_rules": {
      "description": "For electronics (phone, laptop, computer, tablet)",
      "include": ["storage", "ram", "model", "color"],
      "exclude": ["weight", "volume"],
      "reason": "Electronics use technical specs, not weight/volume"
    },
    "jewelry_rules": {
      "description": "For jewelry (necklace, ring, bracelet, watch)",
      "include": ["chain_length", "plating", "gemstone"],
      "exclude": ["size"],
      "reason": "Jewelry uses specific measurements, not generic sizes"
    }
  }
}
```

---

