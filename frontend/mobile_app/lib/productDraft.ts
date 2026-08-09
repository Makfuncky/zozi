import { secureGetItemAsync, secureSetItemAsync, secureDeleteItemAsync } from "@/lib/expoSecureStorage";

const DRAFT_KEY = "zozi_product_draft";

// expo-secure-store limits each value to a small byte budget; keep text fields
// within that budget so a draft never fails to persist.
const NAME_MAX = 200;
const TEXT_MAX = 1600;

function clip(value: string | undefined, max: number): string {
  if (!value) return "";
  return value.length > max ? value.slice(0, max) : value;
}

export interface ProductDraft {
  name: string;
  description: string;
  price: string;
  stock: string;
  category: string;
  subcategory: string;
  color: string;
  tags: string;
  sizes: string;
  return_window_days: string;
  is_active: boolean;
  name_ar?: string;
  description_ar?: string;
  halal_compliance?: boolean;
  modesty_compliance?: boolean;
  weight_kg?: string;
  dimensions?: string;
}

export async function saveProductDraft(draft: ProductDraft): Promise<void> {
  try {
    const payload: ProductDraft = {
      ...draft,
      name: clip(draft.name, NAME_MAX),
      name_ar: clip(draft.name_ar, NAME_MAX),
      description: clip(draft.description, TEXT_MAX),
      description_ar: clip(draft.description_ar, TEXT_MAX),
    };
    await secureSetItemAsync(DRAFT_KEY, JSON.stringify(payload));
  } catch {
    // best-effort persistence
  }
}

export async function loadProductDraft(): Promise<ProductDraft | null> {
  try {
    const raw = await secureGetItemAsync(DRAFT_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as ProductDraft;
  } catch {
    return null;
  }
}

export async function clearProductDraft(): Promise<void> {
  try {
    await secureDeleteItemAsync(DRAFT_KEY);
  } catch {
    // ignore
  }
}

export async function hasProductDraft(): Promise<boolean> {
  try {
    const raw = await secureGetItemAsync(DRAFT_KEY);
    return Boolean(raw);
  } catch {
    return false;
  }
}
