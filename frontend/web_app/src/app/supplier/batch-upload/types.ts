export interface BatchAnalysisItem {
  index: number;
  file: File;
  previewUrl: string;
  status: "pending" | "analyzing" | "completed" | "failed";
  winner_strategy?: string;
  winner_score?: number;
  bg_removed_b64?: string;
  analysis?: {
    product_name_hint?: string;
    suggested_category?: string;
    suggested_subcategory?: string;
    suggested_brand?: string;
    english_description?: string;
    product_description?: string;
    ai_suggested_price?: number;
    suggested_tags?: string[];
    detected_attributes?: { color?: string[]; material?: string[]; brand?: string };
    variant_options?: Record<string, string[]>;
    stock_hints?: Record<string, Record<string, number>>;
    source?: string;
  };
  price_suggestion?: {
    suggested_price?: number;
    price_range?: { min: number; max: number };
  };
  confidence?: number;
  autoPublished?: boolean;
  mergedInto?: number; // index of the survivor item this was merged into
  error?: string;
  // Editable fields (user can override)
  editedName: string;
  editedPrice: number;
  editedStock: number;
  editedCategory: string;
}

export interface BatchAnalyzeResponse {
  total: number;
  completed: number;
  failed: number;
  strategy_wins: Record<string, number>;
  results: Array<{
    status: string;
    name_hint?: string;
    winner_strategy?: string;
    winner_score?: number;
    bg_removed_b64?: string;
    analysis?: Record<string, any>;
    price_suggestion?: Record<string, any>;
    error?: string;
  }>;
}

export interface BatchPublishResponse {
  total: number;
  published: number;
  failed: number;
  products: Array<{
    id: number;
    name: string;
    slug: string;
    image_url: string;
    category: string;
    price: number;
    stock: number;
    variants_count: number;
  }>;
  errors: Array<{
    index: number;
    name: string;
    error: string;
  }>;
  partial?: boolean;
}

export type BatchPageStep = "select" | "analyzing" | "review" | "publishing" | "complete";
