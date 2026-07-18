export interface SupplierVariantTemplate {
  key: string;
  label: string;
  hint: string;
  options: string[];
  customPlaceholder: string;
  materialsPlaceholder: string;
  dimensionsPlaceholder: string;
  weightPlaceholder: string;
}

export const SUPPLIER_VARIANT_TEMPLATES: SupplierVariantTemplate[] = [
  {
    key: "apparel",
    label: "Apparel",
    hint: "Best for fashion, abayas, dresses, shirts, and soft goods with size-based variants.",
    options: ["XS", "S", "M", "L", "XL", "XXL", "XXXL"],
    customPlaceholder: "e.g. 28x30, Tall M, Regular XL",
    materialsPlaceholder: "e.g. Cotton 95%, Elastane 5%",
    dimensionsPlaceholder: "e.g. Folded pack 32 x 24 x 3 cm",
    weightPlaceholder: "e.g. 0.35",
  },
  {
    key: "footwear",
    label: "Footwear",
    hint: "Use for shoes, sandals, heels, slides, or other EU/UK/US-size driven listings.",
    options: ["35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46"],
    customPlaceholder: "e.g. UK 8, Wide Fit 42",
    materialsPlaceholder: "e.g. Leather upper, rubber sole",
    dimensionsPlaceholder: "e.g. Box 34 x 22 x 12 cm",
    weightPlaceholder: "e.g. 0.90",
  },
  {
    key: "kids",
    label: "Kids",
    hint: "For age-band variants used by kidswear, school items, and toddler gear.",
    options: ["2Y", "3Y", "4Y", "5Y", "6Y", "8Y", "10Y", "12Y"],
    customPlaceholder: "e.g. 18-24M, Age 14",
    materialsPlaceholder: "e.g. Soft cotton blend",
    dimensionsPlaceholder: "e.g. Packed size 28 x 20 x 4 cm",
    weightPlaceholder: "e.g. 0.25",
  },
  {
    key: "pack-bundle",
    label: "Pack / Bundle",
    hint: "For promotions, consumables, refill packs, or products sold in counts and bundle sizes.",
    options: ["Single", "Pack of 2", "Pack of 3", "Pack of 6", "Pack of 12", "Bundle"],
    customPlaceholder: "e.g. Family pack, Buy 1 Get 1 set",
    materialsPlaceholder: "e.g. Mixed consumable pack / bundle contents",
    dimensionsPlaceholder: "e.g. Carton 24 x 18 x 10 cm",
    weightPlaceholder: "e.g. 1.20",
  },
  {
    key: "capacity-volume",
    label: "Capacity / Volume",
    hint: "For bottles, cosmetics, food jars, storage, memory sizes, or anything sold by capacity.",
    options: ["100 ml", "250 ml", "500 ml", "1 L", "32 GB", "64 GB", "128 GB"],
    customPlaceholder: "e.g. 750 ml, 256 GB, 2 TB",
    materialsPlaceholder: "e.g. Glass bottle, food-grade plastic",
    dimensionsPlaceholder: "e.g. 10 x 10 x 28 cm",
    weightPlaceholder: "e.g. 0.75",
  },
  {
    key: "model-edition",
    label: "Model / Edition",
    hint: "For electronics, accessories, books, or collectibles where the variant is a model, edition, or compatibility set.",
    options: ["Standard", "Pro", "Max", "2026 Edition", "Type-C", "Lightning"],
    customPlaceholder: "e.g. iPhone 15 Pro, Matte Black edition",
    materialsPlaceholder: "e.g. ABS shell, aluminum frame",
    dimensionsPlaceholder: "e.g. Device 15 x 8 x 1 cm",
    weightPlaceholder: "e.g. 0.18",
  },
  {
    key: "home-furniture",
    label: "Home / Furniture",
    hint: "For furniture, decor, and homeware where dimensions or size tiers matter more than apparel sizing.",
    options: ["Small", "Medium", "Large", "2-Seater", "3-Seater", "King", "Queen"],
    customPlaceholder: "e.g. 120 x 80 cm, Set of 4",
    materialsPlaceholder: "e.g. Solid wood, steel, tempered glass",
    dimensionsPlaceholder: "e.g. 180 x 90 x 75 cm",
    weightPlaceholder: "e.g. 18.5",
  },
  {
    key: "universal",
    label: "Universal",
    hint: "Fallback template for products that only need one option or a few simple custom variants.",
    options: ["One Size", "Mini", "Standard", "Large", "Universal Fit"],
    customPlaceholder: "e.g. Limited edition, Region plug, Left / Right",
    materialsPlaceholder: "e.g. Add main material or composition",
    dimensionsPlaceholder: "e.g. 30 x 20 x 10 cm",
    weightPlaceholder: "e.g. 0.50",
  },
];

export function getSupplierVariantTemplate(key?: string | null): SupplierVariantTemplate | undefined {
  return SUPPLIER_VARIANT_TEMPLATES.find((template) => template.key === key);
}

export function suggestSupplierVariantTemplate(input: {
  category?: string | null;
  name?: string | null;
  tags?: string | null;
}): string {
  const text = `${input.category || ""} ${input.name || ""} ${input.tags || ""}`.toLowerCase();

  if (/(shoe|sneaker|heel|sandal|slipper|boot)/.test(text)) return "footwear";
  if (/(kid|baby|toddler|child|children|school)/.test(text)) return "kids";
  if (/(dress|shirt|hoodie|abaya|fashion|jean|pant|coat|jacket|wear)/.test(text)) return "apparel";
  if (/(bundle|pack|set of|refill|combo|deal)/.test(text)) return "pack-bundle";
  if (/(ml|liter|litre|l\b|gb|tb|capacity|storage|volume)/.test(text)) return "capacity-volume";
  if (/(phone|laptop|earbud|headphone|charger|case|model|edition|compatible|electronics)/.test(text)) return "model-edition";
  if (/(furniture|home|sofa|table|chair|mattress|bed|cabinet|decor)/.test(text)) return "home-furniture";
  return "universal";
}