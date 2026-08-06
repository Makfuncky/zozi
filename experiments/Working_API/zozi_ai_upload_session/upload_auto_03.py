#!/usr/bin/env python3
"""
ZOZI Enterprise Product Upload Engine - INTELLIGENT VERSION
============================================================
✅ Product-Type Intelligence (Liquid vs Solid vs Electronic vs Furniture)
✅ Mutual Exclusion Rules (No volume+weight, no size+dimensions)
✅ Smart Variant Selection (AI understands what each product needs)
✅ Fixed "empty string" bug
✅ Fixed dimensions prompt (actual measurements, not S/M/L)
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
from dataclasses import dataclass, field
import httpx
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class Config:
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5"
    OLLAMA_VISION_MODEL: str = "moondream"
    
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "zozi_db")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    
    USE_DATABASE: bool = False
    OUTPUT_DIR: str = "products_output"
    
    @classmethod
    async def validate(cls):
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
# MASTER ATTRIBUTE DATABASE - INTELLIGENT VERSION
# ============================================================================

class MasterAttributeDatabase:
    """
    FIXED: Smart variant definitions with product-type intelligence
    """
    
    VARIANTS = {
        # ========================================
        # FASHION & APPAREL
        # ========================================
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
            "product_types": ["clothing", "electronic", "furniture", "appliance", "accessory"]
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
            "mutually_exclusive_with": ["dimensions"]  # Can't have both size and dimensions!
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
            "product_types": ["clothing", "furniture", "jewelry", "appliance"]
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
            "product_types": ["clothing"]
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
            "product_types": ["clothing", "shoes", "accessory"]
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
            "product_types": ["clothing"]
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
            "product_types": ["clothing"]
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
            "product_types": ["clothing"]
        },
        
        # ========================================
        # ELECTRONICS & COMPUTERS
        # ========================================
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
            "product_types": ["electronic"]
        },
        "ram": {
            "name": "RAM",
            "name_ar": "الذاكرة العشوائية",
            "prompt": "💻 RAM options (comma-sep, e.g., 4GB, 8GB, 16GB, 32GB, 64GB)",
            "type": "text",
            "categories": [
                "electronics", "laptops", "desktops", "computers", "tablets"
            ],
            "product_types": ["electronic"]
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
            "product_types": ["electronic", "automotive"]
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
            "product_types": ["electronic"]
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
            "product_types": ["electronic"]
        },
        "processor": {
            "name": "Processor",
            "name_ar": "المعالج",
            "prompt": "⚙️ Processor options (comma-sep, e.g., Intel i5, Intel i7, AMD Ryzen 5, M1, M2)",
            "type": "text",
            "categories": [
                "electronics", "laptops", "desktops", "computers", "tablets"
            ],
            "product_types": ["electronic"]
        },
        
        # ========================================
        # JEWELRY & WATCHES
        # ========================================
        "chain_length": {
            "name": "Chain Length",
            "name_ar": "طول السلسلة",
            "prompt": "📏 Chain lengths in inches (comma-sep, e.g., 16, 18, 20, 22, 24, 30)",
            "type": "text",
            "categories": [
                "jewelry", "necklaces", "pendants", "chains", "accessories"
            ],
            "product_types": ["jewelry"]
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
            "product_types": ["jewelry"]
        },
        "watch_strap": {
            "name": "Watch Strap",
            "name_ar": "سوار الساعة",
            "prompt": "⌚ Watch strap types (comma-sep, e.g., Leather, Metal, Silicone, Nylon, Rubber, Ceramic)",
            "type": "text",
            "categories": [
                "watches", "jewelry", "smartwatches", "wearables", "accessories"
            ],
            "product_types": ["jewelry", "electronic"]
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
            "product_types": ["jewelry"]
        },
        "ring_size": {
            "name": "Ring Size",
            "name_ar": "مقاس الخاتم",
            "prompt": "💍 Ring sizes (comma-sep, e.g., 5, 6, 7, 8, 9, 10, 11, 12)",
            "type": "text",
            "categories": [
                "jewelry", "rings", "accessories"
            ],
            "product_types": ["jewelry"]
        },
        "bracelet_size": {
            "name": "Bracelet Size",
            "name_ar": "مقاس السوار",
            "prompt": "📿 Bracelet sizes (comma-sep, e.g., Small, Medium, Large, 6.5 inch, 7 inch, 7.5 inch)",
            "type": "text",
            "categories": [
                "jewelry", "bracelets", "watches", "accessories"
            ],
            "product_types": ["jewelry"]
        },
        
        # ========================================
        # BEAUTY & GROCERIES - FIXED WITH PRODUCT TYPE RULES
        # ========================================
        "scent": {
            "name": "Scent/Fragrance",
            "name_ar": "العطر",
            "prompt": "🌸 Available scents (comma-sep, e.g., Rose, Oud, Vanilla, Jasmine, Lavender, Citrus)",
            "type": "text",
            "categories": [
                "beauty", "perfumes", "home", "candles", "air fresheners",
                "cosmetics", "skincare", "haircare"
            ],
            "product_types": ["beauty"]
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
            "product_types": ["food"]
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
            "product_types": ["food_solid"],  # ONLY for solid food!
            "mutually_exclusive_with": ["volume"]  # Can't have both weight and volume!
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
            "product_types": ["liquid"],  # ONLY for liquids!
            "mutually_exclusive_with": ["weight"]  # Can't have both volume and weight!
        },
        "skin_type": {
            "name": "Skin Type",
            "name_ar": "نوع البشرة",
            "prompt": "🧴 Skin type options (comma-sep, e.g., All Skin Types, Oily, Dry, Sensitive, Combination)",
            "type": "text",
            "categories": [
                "beauty", "cosmetics", "skincare", "haircare"
            ],
            "product_types": ["beauty"]
        },
        
        # ========================================
        # HOME & APPLIANCES - FIXED DIMENSIONS
        # ========================================
        "capacity": {
            "name": "Capacity",
            "name_ar": "السعة",
            "prompt": "📦 Capacity options (comma-sep, e.g., 50L, 100L, 200L, 300L, 500L, 1000L)",
            "type": "text",
            "categories": [
                "home", "appliances", "refrigerators", "washing machines",
                "ovens", "microwaves", "dishwashers", "air conditioners"
            ],
            "product_types": ["appliance"]
        },
        "voltage": {
            "name": "Voltage",
            "name_ar": "الجهد",
            "prompt": "⚡ Voltage options (comma-sep, e.g., 110V, 220V, 240V, 380V)",
            "type": "text",
            "categories": [
                "electronics", "appliances", "home", "tools", "machinery"
            ],
            "product_types": ["appliance", "electronic"]
        },
        "wattage": {
            "name": "Wattage",
            "name_ar": "القدرة",
            "prompt": "💡 Wattage options (comma-sep, e.g., 40W, 60W, 100W, 150W, 500W, 1000W, 2000W)",
            "type": "text",
            "categories": [
                "electronics", "appliances", "lighting", "home", "tools"
            ],
            "product_types": ["appliance", "electronic"]
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
            "product_types": ["furniture", "appliance"],  # For furniture and large appliances
            "mutually_exclusive_with": ["size"]  # Can't have both dimensions and size!
        },
        "color_temperature": {
            "name": "Color Temperature",
            "name_ar": "درجة حرارة اللون",
            "prompt": "💡 Color temperature options (comma-sep, e.g., Warm White, Cool White, Daylight, RGB)",
            "type": "text",
            "categories": [
                "lighting", "home", "electronics", "led", "bulbs"
            ],
            "product_types": ["appliance"]
        },
        
        # ========================================
        # TOYS & KIDS
        # ========================================
        "age_group": {
            "name": "Age Group",
            "name_ar": "الفئة العمرية",
            "prompt": "👶 Age groups (comma-sep, e.g., 0-2 Years, 3-5 Years, 6-8 Years, 9-12 Years, Teens)",
            "type": "text",
            "categories": [
                "toys", "kids", "baby", "children", "games", "puzzles",
                "educational", "outdoor", "sports"
            ],
            "product_types": ["toy"]
        },
        "toy_type": {
            "name": "Toy Type",
            "name_ar": "نوع اللعبة",
            "prompt": "🧸 Toy type options (comma-sep, e.g., Action Figures, Dolls, Building Blocks, Vehicles, Puzzles)",
            "type": "text",
            "categories": [
                "toys", "kids", "baby", "children", "games"
            ],
            "product_types": ["toy"]
        },
        
        # ========================================
        # AUTOMOTIVE
        # ========================================
        "car_fitment": {
            "name": "Car Fitment",
            "name_ar": "توافق السيارة",
            "prompt": "🚗 Car models this fits (comma-sep, e.g., Toyota Camry 2018-2022, Nissan Altima, Honda Accord)",
            "type": "text",
            "categories": [
                "automotive", "car_parts", "accessories", "tires",
                "batteries", "oil", "filters", "brakes", "suspension"
            ],
            "product_types": ["automotive"]
        },
        "vehicle_type": {
            "name": "Vehicle Type",
            "name_ar": "نوع المركبة",
            "prompt": "🏍️ Vehicle types (comma-sep, e.g., Car, SUV, Truck, Motorcycle, Bicycle, Van)",
            "type": "text",
            "categories": [
                "automotive", "accessories", "tires", "parts"
            ],
            "product_types": ["automotive"]
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
            "product_types": ["automotive", "electronic", "appliance"]
        },
        
        # ========================================
        # SPORTS & OUTDOOR
        # ========================================
        "sport_type": {
            "name": "Sport Type",
            "name_ar": "نوع الرياضة",
            "prompt": "⚽ Sport type options (comma-sep, e.g., Football, Basketball, Tennis, Swimming, Running, Cycling)",
            "type": "text",
            "categories": [
                "sports", "outdoor", "fitness", "gym", "equipment"
            ],
            "product_types": ["sport"]
        },
        
        # ========================================
        # BOOKS & STATIONERY
        # ========================================
        "language": {
            "name": "Language",
            "name_ar": "اللغة",
            "prompt": "🌐 Language options (comma-sep, e.g., English, Arabic, French, Spanish, Chinese)",
            "type": "text",
            "categories": [
                "books", "stationery", "educational", "magazines"
            ],
            "product_types": ["book"]
        },
        "binding": {
            "name": "Binding",
            "name_ar": "الغلاف",
            "prompt": "📚 Binding options (comma-sep, e.g., Hardcover, Paperback, Spiral, eBook)",
            "type": "text",
            "categories": [
                "books", "stationery", "educational"
            ],
            "product_types": ["book"]
        }
    }
    
    # Product type classification rules
    PRODUCT_TYPE_KEYWORDS = {
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
    }
    
    @classmethod
    def classify_product_type(cls, product_name: str, category: str, subcategory: str) -> str:
        """Classify product into a type for intelligent variant selection"""
        text = f"{product_name} {category} {subcategory}".lower()
        
        # Check each product type
        for product_type, keywords in cls.PRODUCT_TYPE_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return product_type
        
        # Fallback based on category
        category_lower = category.lower()
        if any(kw in category_lower for kw in ["fashion", "apparel", "clothing"]):
            return "clothing"
        elif "electronics" in category_lower:
            return "electronic"
        elif "furniture" in category_lower:
            return "furniture"
        elif "home" in category_lower or "appliance" in category_lower:
            return "appliance"
        elif "jewelry" in category_lower:
            return "jewelry"
        elif "beauty" in category_lower:
            return "beauty"
        elif "groceries" in category_lower or "food" in category_lower:
            return "food_solid"  # Default to solid food
        elif "toys" in category_lower:
            return "toy"
        elif "books" in category_lower:
            return "book"
        elif "automotive" in category_lower:
            return "automotive"
        
        return "general"
    
    @classmethod
    def get_allowed_variants(cls, category: str, subcategory: str) -> List[str]:
        """Get list of allowed variants for a category"""
        category_lower = category.lower().strip()
        subcategory_lower = subcategory.lower().strip()
        
        allowed = []
        
        # Strategy 1: Exact match
        for variant_key, variant_data in cls.VARIANTS.items():
            if category_lower in variant_data["categories"] or \
               subcategory_lower in variant_data["categories"]:
                allowed.append(variant_key)
        
        # Strategy 2: Partial match
        if not allowed:
            for variant_key, variant_data in cls.VARIANTS.items():
                for cat in variant_data["categories"]:
                    if category_lower in cat or cat in category_lower or \
                       subcategory_lower in cat or cat in subcategory_lower:
                        if variant_key not in allowed:
                            allowed.append(variant_key)
        
        # Strategy 3: Keyword-based fallback
        if not allowed:
            if any(kw in category_lower or kw in subcategory_lower for kw in ["apparel", "clothing", "fashion", "shirt", "t-shirt"]):
                allowed = ["color", "size", "material", "pattern", "gender"]
            elif any(kw in category_lower or kw in subcategory_lower for kw in ["electronics", "phone", "laptop"]):
                allowed = ["color", "storage", "ram", "model", "screen_size"]
            elif any(kw in category_lower or kw in subcategory_lower for kw in ["jewelry", "ring", "necklace"]):
                allowed = ["color", "material", "plating", "size"]
            elif any(kw in category_lower or kw in subcategory_lower for kw in ["home", "furniture"]):
                allowed = ["color", "material", "dimensions", "capacity"]
            elif any(kw in category_lower or kw in subcategory_lower for kw in ["beauty", "cosmetic"]):
                allowed = ["color", "volume", "weight", "scent", "skin_type"]
            elif any(kw in category_lower or kw in subcategory_lower for kw in ["groceries", "food"]):
                allowed = ["flavor", "weight", "volume"]
            elif any(kw in category_lower or kw in subcategory_lower for kw in ["toy", "game", "kids"]):
                allowed = ["color", "size", "age_group"]
            elif any(kw in category_lower or kw in subcategory_lower for kw in ["automotive", "car"]):
                allowed = ["color", "car_fitment", "vehicle_type", "year"]
        
        # Strategy 4: Ultimate fallback
        if not allowed:
            logger.warning("⚠️  No variants found. Using universal fallback.")
            allowed = ["color"]
        
        return allowed
    
    @classmethod
    def get_variant_info(cls, variant_key: str) -> Dict[str, Any]:
        """Get full information about a variant"""
        return cls.VARIANTS.get(variant_key, {})
    
    @classmethod
    def get_mutually_exclusive(cls, variant_key: str) -> List[str]:
        """Get variants that are mutually exclusive with this one"""
        variant_info = cls.VARIANTS.get(variant_key, {})
        return variant_info.get("mutually_exclusive_with", [])
    
    @classmethod
    def get_all_variant_keys(cls) -> List[str]:
        """Get all available variant keys"""
        return list(cls.VARIANTS.keys())


# ============================================================================
# DATABASE CONNECTION
# ============================================================================

class DatabaseConnection:
    def __init__(self, config: Config):
        self.config = config
        self.connection = None
    
    async def connect(self):
        if not self.config.USE_DATABASE:
            logger.info("ℹ️  Database mode disabled - using fallback master attributes")
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
        if self.connection:
            await self.connection.close()
            logger.info("🔌 Database connection closed")
    
    async def get_allowed_variants(self, category: str, subcategory: str) -> List[str]:
        if not self.connection:
            return MasterAttributeDatabase.get_allowed_variants(category, subcategory)
        
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
                return MasterAttributeDatabase.get_allowed_variants(category, subcategory)
                
        except Exception as e:
            logger.error(f"❌ Database query failed: {e}. Using fallback.")
            return MasterAttributeDatabase.get_allowed_variants(category, subcategory)
    
    async def save_product(self, product_data: Dict, descriptions: Dict, 
                          image_analysis: Dict, image_paths: List[str], 
                          supplier_id: str) -> str:
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
# AI SERVICES - INTELLIGENT VERSION
# ============================================================================

class AIService:
    def __init__(self, config: Config):
        self.config = config
        self.client = httpx.AsyncClient(
            base_url=f"{config.OLLAMA_BASE_URL}/v1",
            headers={"Content-Type": "application/json"},
            timeout=300.0
        )
    
    def encode_image(self, image_path: str) -> str:
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
            
            # FIXED: Use null instead of "empty string"
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
            
            # FIXED: Filter out null, None, empty strings, and "empty string" literal
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
        product_type = MasterAttributeDatabase.classify_product_type(
            product_name, category, subcategory
        )
        logger.info(f"📦 Product type classified as: {product_type}")
        
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
   - Example: Olive oil → volume only (500ml, 1L), NOT weight

2. SOLID FOOD (rice, flour, sugar, spices, coffee, tea, snacks):
   - ONLY ask for "weight" (g/kg)
   - NEVER ask for "volume" (solids are measured by weight, not volume)
   - Example: Rice → weight only (1kg, 5kg), NOT volume

3. FURNITURE (cupboard, cabinet, table, chair, sofa, bed):
   - ONLY ask for "dimensions" (actual measurements in cm)
   - NEVER ask for "size" (Small/Medium/Large doesn't make sense for furniture)
   - Example: Cupboard → dimensions (180cm x 60cm x 40cm), NOT size (S/M/L)

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
                exclusive_with = MasterAttributeDatabase.get_mutually_exclusive(variant)
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
        await self.client.aclose()


# ============================================================================
# SMART INTERVIEW SERVICE
# ============================================================================

class SmartInterviewService:
    async def conduct_interview(
        self,
        image_analysis: Dict,
        relevant_variants: List[str],
        confirmations: Dict[str, str]
    ) -> Dict[str, Any]:
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
                variant_info = MasterAttributeDatabase.get_variant_info(key)
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
                variant_info = MasterAttributeDatabase.get_variant_info(variant_key)
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
    def __init__(self, config: Config):
        self.config = config
        self.ai = AIService(config)
        self.db = DatabaseConnection(config)
        self.interview = SmartInterviewService()
        self.csv_exporter = CSVExporter(config.OUTPUT_DIR)
    
    async def initialize(self):
        if self.config.USE_DATABASE:
            await self.db.connect()
    
    async def upload_product(
        self,
        image_paths: List[str],
        supplier_id: str
    ) -> Dict[str, Any]:
        logger.info("=" * 70)
        logger.info("🚀 STARTING ZOZI PRODUCT UPLOAD - INTELLIGENT VERSION")
        logger.info("=" * 70)
        
        # Step 1: AI Vision
        logger.info("\n🔍 STEP 1: Analyzing image...")
        image_analysis = await self.ai.analyze_image(image_paths[0])
        
        # Step 2: Database - Get allowed variants
        logger.info("\n📊 STEP 2: Fetching allowed variants from database...")
        allowed_variants = await self.db.get_allowed_variants(
            image_analysis.get("category"),
            image_analysis.get("subcategory")
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
        await self.ai.close()
        await self.db.close()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    try:
        await Config.validate()
    except Exception as e:
        print(f"\n❌ {e}")
        return
    
    print("\n" + "=" * 70)
    print("🧪 ZOZI ENTERPRISE PRODUCT UPLOAD SYSTEM - INTELLIGENT VERSION")
    print("=" * 70)
    
    path = input("\n📸 Enter product image path: ").strip().strip('"').strip("'")
    
    if not path or not os.path.exists(path):
        print(f"❌ File not found: {path}")
        return
    
    supplier_id = input("\n👤 Supplier ID [supplier_001]: ").strip() or "supplier_001"
    
    config = Config()
    orchestrator = ProductUploadOrchestrator(config)
    
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
    ║   🧠 INTELLIGENT VERSION                                  ║
    ║                                                           ║
    ║   ✅ Product-Type Intelligence (Liquid vs Solid vs etc)  ║
    ║   ✅ Mutual Exclusion Rules (No volume+weight)            ║
    ║   ✅ Smart Variant Selection                              ║
    ║   ✅ Fixed "empty string" bug                             ║
    ║   ✅ Fixed dimensions prompt (actual measurements)        ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(main())