export const SUPPLIER_CATEGORIES = [
  "Electronics", "Fashion", "Accessories", "Furniture", "Beauty",
  "Sports", "Home", "Books", "Baby", "Automotive", "Crafts",
  "Grocery", "Health", "Toys", "Jewelry", "Office", "General",
];

export const SUPPLIER_SUBCATEGORY_OPTIONS: Record<string, string[]> = {
  Electronics: ["Audio", "Mobile Phones", "Computers", "Accessories", "Gaming", "Smart Home"],
  Fashion: ["Abayas", "Dresses", "Tops", "Bottoms", "Outerwear", "Modest Wear"],
  Accessories: ["Bags", "Belts", "Scarves", "Watches", "Travel"],
  Furniture: ["Chairs", "Tables", "Sofas", "Storage", "Bedroom", "Lighting"],
  Beauty: ["Skincare", "Haircare", "Makeup", "Fragrance", "Beauty Tools"],
  Sports: ["Training", "Outdoor", "Recovery", "Team Sports", "Fitness Gear"],
  Home: ["Kitchen", "Decor", "Bedding", "Bath", "Storage", "Dining"],
  Books: ["Business", "Lifestyle", "Children", "Education", "Religion"],
  Baby: ["Feeding", "Nursery", "Travel", "Clothing", "Toys"],
  Automotive: ["Interior", "Exterior", "Care", "Electronics", "Safety"],
  Crafts: ["DIY Kits", "Art Supplies", "Fabric", "Stationery", "Seasonal"],
  Grocery: ["Snacks", "Beverages", "Pantry", "Organic", "Bulk Packs"],
  Health: ["Supplements", "Wellness", "Personal Care", "Mobility", "Monitoring"],
  Toys: ["Educational", "Collectibles", "Outdoor Play", "Board Games", "Plush"],
  Jewelry: ["Rings", "Necklaces", "Bracelets", "Earrings", "Gift Sets"],
  Office: ["Desks", "Organization", "Writing", "Tech", "Supplies"],
  General: ["Best Sellers", "New Arrivals", "Seasonal", "Bundles", "Essentials"],
};

const COLOR_ALIASES: Record<string, string> = {
  gray: "Grey",
  grey: "Grey",
  "dark blue": "Navy",
  "light blue": "Blue",
  "off white": "Ivory",
  "off-white": "Ivory",
};

export function resolveKnownCategory(value?: string | null): string {
  const normalized = String(value || "").trim().toLowerCase();
  return SUPPLIER_CATEGORIES.find((category) => category.toLowerCase() === normalized) || "General";
}

export function normalizeSuggestedColor(value?: string | null): string {
  const normalized = String(value || "").trim();
  if (!normalized) return "";
  const alias = COLOR_ALIASES[normalized.toLowerCase()];
  if (alias) return alias;
  return normalized
    .split(/\s+/)
    .filter(Boolean)
    .map((segment) => `${segment.charAt(0).toUpperCase()}${segment.slice(1).toLowerCase()}`)
    .join(" ");
}

export function inferSuggestedSubCategory(category: string, source: string, currentValue = ""): string {
  const options = SUPPLIER_SUBCATEGORY_OPTIONS[category] ?? [];
  if (options.length === 0) return currentValue;

  const normalizedSource = source.toLowerCase();
  const aliases: Record<string, string[]> = {
    Audio: ["audio", "earbud", "earphone", "headphone", "speaker"],
    "Mobile Phones": ["mobile", "phone", "iphone", "android"],
    Computers: ["computer", "laptop", "monitor", "keyboard"],
    Gaming: ["gaming", "console", "controller"],
    "Smart Home": ["smart home", "automation"],
    Accessories: ["charger", "case", "adapter"],
    Abayas: ["abaya"],
    Dresses: ["dress", "gown"],
    Tops: ["top", "shirt", "tee", "t-shirt", "blouse", "bra", "lingerie", "bikini"],
    Bottoms: ["pant", "trouser", "skirt", "short", "jean"],
    Outerwear: ["jacket", "coat", "hoodie"],
    Chairs: ["chair", "stool", "seat"],
    Tables: ["table", "desk"],
    Sofas: ["sofa", "couch", "chaise", "sectional"],
    Storage: ["storage", "cupboard", "cabinet", "wardrobe", "dresser"],
    Bedroom: ["bedroom", "bed", "nightstand", "mattress"],
    Lighting: ["lamp", "lighting", "light"],
    Skincare: ["skin", "serum", "cream", "skincare"],
    Makeup: ["makeup", "lip", "mascara", "palette"],
    Haircare: ["hair", "shampoo", "conditioner"],
  };

  const aliasMatch = options.find((option) => {
    const keywords = aliases[option] ?? [option.toLowerCase()];
    return keywords.some((keyword) => normalizedSource.includes(keyword.toLowerCase()));
  });
  if (aliasMatch) return aliasMatch;

  const directMatch = options.find((option) => normalizedSource.includes(option.toLowerCase()));
  if (directMatch) return directMatch;

  const currentMatch = options.find((option) => option.toLowerCase() === currentValue.trim().toLowerCase());
  return currentMatch || options[0] || "";
}

export function mergeVariantOptions(nextOptions: unknown, currentValue: string): string {
  if (!Array.isArray(nextOptions)) return currentValue;
  const normalized = nextOptions
    .map((item) => String(item || "").trim())
    .filter(Boolean);
  return normalized.length > 0 ? Array.from(new Set(normalized)).join(", ") : currentValue;
}