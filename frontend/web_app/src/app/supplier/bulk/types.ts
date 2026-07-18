export const CATEGORIES = [
  "Electronics", "Fashion", "Accessories", "Furniture", "Beauty",
  "Sports", "Home", "Books", "Baby", "Automotive", "Crafts",
  "Grocery", "Health", "Toys", "Jewelry", "Office", "General",
];

export const CATEGORY_SUBCATEGORY_OPTIONS: Record<string, string[]> = {
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

export const VARIANT_SHAPE_OPTIONS = [
  "Round",
  "Square",
  "Rectangular",
  "Oval",
  "Slim",
  "Wide",
  "Tall",
  "Compact",
];

export const SUPPORTED_CURRENCIES = ["OMR", "AED", "SAR", "QAR", "KWD", "BHD", "USD", "EUR", "GBP", "PKR", "INR"];

export interface DraftVariant {
  id: string;
  title: string;
  size: string;
  color: string;
  shape: string;
  productCode: string;
  price: string;
  stock: string;
  mediaMode: "upload" | "url";
  mediaFile: File | null;
  mediaUrl: string;
  mediaPreview: string | null;
  isActive: boolean;
}

export interface ProductDraft {
  id: string;
  name: string;
  price: string;
  currencyCode: string;
  returnWindowDays: string;
  isActive: boolean;
  stock: string;
  category: string;
  subCategory: string;
  description: string;
  brand: string;
  color: string;
  tags: string;
  visibilityRegions: string[];
  videoMode: "upload" | "url";
  videoFile: File | null;
  videoUrl: string;
  videoPreview: string | null;
  imageMode: "upload" | "url";
  imageFile: File | null;
  imagePreview: string | null;
  imageUrl: string;
  extraImageUrls: string[];
  additionalImageFiles: (File | null)[];
  selectedSizeGroup: string;
  selectedSizes: string[];
  customSizes: string;
  selectedShapes: string[];
  customShapes: string;
  variants: DraftVariant[];
  materials: string;
  weight: string;
  dimensions: string;
  expanded: boolean;
}

export interface UploadResult {
  created_count: number;
  error_count: number;
  products: Array<{ id: number; name: string; category: string; tags: string }>;
  errors: Array<{
    index: number;
    name?: string;
    error: string;
    field_key?: string;
    variant_index?: number;
    variant_field_key?: string;
  }>;
  ai_used: boolean;
}

export interface DraftValidationIssue {
  message: string;
  focusId: string;
  step: number;
}

export const INITIAL_DRAFT_ID = "draft-initial";
