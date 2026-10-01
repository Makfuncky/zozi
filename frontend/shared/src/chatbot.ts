/**
 * Shared chatbot utilities for web and mobile clients.
 * Keeps intent parsing and fallback response routing consistent across platforms.
 */

export interface ChatbotSearchResult {
  id: number;
  name: string;
  price: number;
  rating?: number;
  image_url?: string | null;
  category?: string | null;
  brand?: string | null;
  color?: string | null;
  sizes?: string[];
  stock?: number;
}

export type ChatbotResultMode = "exact" | "close" | "none";

export interface ChatbotResponsePayload {
  reply: string;
  intent: string;
  products: ChatbotSearchResult[];
  session_id?: string;
  suggested_prompts?: string[];
  result_mode?: ChatbotResultMode;
}

export type ChatbotReplyKey =
  | "chatbotGreeting"
  | "chatbotHelpReply"
  | "chatbotOrderReply"
  | "chatbotShippingReply"
  | "chatbotReturnReply"
  | "chatbotPaymentReply"
  | "chatbotSupplierReply"
  | "chatbotWishlistReply"
  | "chatbotOfferReply"
  | "chatbotUnknownReply";

const CHATBOT_REPLY_PATTERNS: ReadonlyArray<readonly [RegExp, ChatbotReplyKey]> = [
  [/^(hi|hello|hey|salaam|hola|مرحبا|السلام عليكم)\b/i, "chatbotGreeting"],
  [/help|support/i, "chatbotHelpReply"],
  [/order|purchase/i, "chatbotOrderReply"],
  [/ship|deliver/i, "chatbotShippingReply"],
  [/return|refund/i, "chatbotReturnReply"],
  [/pay|card|stripe|tap/i, "chatbotPaymentReply"],
  [/supplier|sell/i, "chatbotSupplierReply"],
  [/wishlist/i, "chatbotWishlistReply"],
  [/offer|discount|deal|coupon/i, "chatbotOfferReply"],
] as const;

const PRODUCT_INTENT = /\b(find|show|search|looking for|recommend|suggest|any|cheapest?|best|top|latest|new|under|over|between)\b/i;
const PRODUCT_NOISE = /\b(order|ship|return|refund|pay|support|help|wishlist|supplier|sell|offer|discount|deal)\b/i;

export function hasProductIntent(message: string): boolean {
  const normalized = String(message || "").trim();
  if (!normalized) return false;
  return PRODUCT_INTENT.test(normalized) && !PRODUCT_NOISE.test(normalized);
}

export function getChatbotReplyKey(message: string): ChatbotReplyKey {
  const normalized = String(message || "");
  for (const [pattern, key] of CHATBOT_REPLY_PATTERNS) {
    if (pattern.test(normalized)) {
      return key;
    }
  }
  return "chatbotUnknownReply";
}

export function extractChatbotSearchResults(payload: unknown): ChatbotSearchResult[] {
  if (!payload || typeof payload !== "object") return [];
  const candidate = payload as { products?: unknown; results?: unknown };
  const products = Array.isArray(candidate.products)
    ? candidate.products
    : Array.isArray(candidate.results)
    ? candidate.results
    : [];
  return products as ChatbotSearchResult[];
}
