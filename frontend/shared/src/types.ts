/* ============================================================
   Shared TypeScript interfaces
   ============================================================ */

export interface Product {
  id: number;
  name: string;
  description: string;
  price: number | string;
  discount_percentage?: number | string | null;
  category: string;
  subcategory?: string | null;
  brand?: string;
  rating?: number;
  image_url: string;
  video_url?: string | null;
  stock: number;
  color?: string;
  tags?: string;           // comma-separated AI-generated tags
  ai_description?: string; // AI-generated description
  sizes?: string;          // JSON array string: ["S","M","L","XL"]
  materials?: string;      // "Cotton, Polyester"
  visibility_regions?: string[];
  additional_images?: string; // JSON array of image paths
  weight?: number;         // in kg
  dimensions?: string;     // "30x20x10 cm"
  supplier?: string;
  supplier_id?: number;
  supplier_badge?: string | null;
  supplier_trusted?: boolean;
  compare_price?: number | string | null;
  discount_starts_at?: string | null;
  discount_ends_at?: string | null;
  offer_type?: string | null;
  offer_title?: string | null;
  offer_discount_pct?: number | string | null;
  offer_starts_at?: string | null;
  offer_ends_at?: string | null;
  flash_sale_id?: number | null;
  sales_count?: number;
  revenue?: number;
  is_deleted?: boolean;
  is_active?: boolean;
  is_verified?: boolean;
  is_hot?: boolean | null;      // admin-pinned HOT badge
  is_featured?: boolean | null; // admin-pinned FEATURED badge
  is_new?: boolean | null;      // supplier/admin-pinned NEW badge
  return_window_days?: number | null;
  created_at?: string;
  updated_at?: string;
  variants?: ProductVariant[];
  isNew?: boolean;
  isFeatured?: boolean;
  reviews?: Review[];
  slug_hash?: string | null; // opaque short link for sharing/affiliate
  primary?: string | null;    // primary badge text (e.g. "Best Seller", "Featured")
}

export interface OrderItem {
  id?: number;
  product_id: number;
  product_name?: string;
  quantity: number;
  price: number;
  image_url?: string;
  selected_size?: string;
  selected_color?: string;
  product?: Product;
}

export interface Order {
  id: number;
  user_id: number;
  items: OrderItem[];
  subtotal_amount?: number;
  discount_amount?: number;
  total_amount: number;
  total?: number; // alias for compatibility
  coupon_code?: string;
  status: string;
  status_label?: string;
  shipping_address?: string;
  customer_phone?: string;
  delivery_location?: string;
  delivery_note?: string;
  shipping_amount?: number;
  vat_amount?: number;
  payment_intent_id?: string;
  payment_method?: string;
  tracking_number?: string;
  paid_at?: string;
  created_at: string;
  updated_at?: string;
}

export interface InventoryItem {
  id: number;
  product_id: number;
  product_name: string;
  sku: string;
  quantity: number;
  status: "in_stock" | "low_stock" | "out_of_stock" | "overstock";
  last_updated: string;
}

export interface Payout {
  id: number;
  amount: number;
  status: string;
  method?: string;
  reference?: string;
  notes?: string;
  created_at: string;
  processed_at?: string;
}

export interface Review {
  id: number;
  user_id: number;
  username?: string;
  rating: number;
  comment?: string;
  is_verified_purchase?: boolean;
  created_at: string;
}

export interface Notification {
  id: number;
  type: string;
  title: string;
  message: string;
  read: boolean;
  link?: string;
  created_at: string;
}

export interface Category {
  id: number;
  name: string;
  slug: string;
  icon?: string;
  image_url?: string;
  parent_id?: number;
  sort_order: number;
  is_active: boolean;
}

export interface Coupon {
  id: number;
  code: string;
  discount_type: "percent" | "fixed";
  value: number;
  min_order: number;
  max_uses?: number;
  uses_count: number;
  expires_at?: string;
  is_active: boolean;
}

export interface WishlistEntry {
  id: number;
  product_id: number;
  product: Product;
  created_at: string;
}

export interface ProductVariant {
  id: number;
  product_id: number;
  title?: string | null;
  sku?: string;
  barcode?: string | null;
  product_code?: string | null;
  size?: string;
  color?: string;
  material?: string;
  price?: number;
  effective_price?: number;
  stock: number;
  media_url?: string | null;
  attributes?: Record<string, string>;
  is_active: boolean;
  sort_order?: number;
  created_at: string;
  updated_at?: string;
}

export interface ReturnRequest {
  id: number;
  order_id: number;
  order_item_id?: number | null;
  user_id: number;
  intent: "return" | "replacement";
  reason: string;
  status: "pending" | "approved" | "rejected" | "completed" | "refunded";
  refund_amount?: number;
  notes?: string;
  resolution_notes?: string | null;
  items?: Array<{ order_item_id?: number | null; product_id: number; product_name: string; quantity: number; price: number; return_window_days?: number | null }>;
  return_window_days?: number | null;
  delivered_at?: string | null;
  return_deadline?: string | null;
  created_at: string;
  updated_at?: string;
}

export interface SupplierDocument {
  id: number;
  supplier_id: number;
  document_type: string;
  file_url: string;
  file_name?: string;
  status: "pending" | "approved" | "rejected";
  notes?: string;
  uploaded_at: string;
  reviewed_at?: string;
}

export interface LogisticsPartner {
  id: number;
  name: string;
  code: string;
  contact_name?: string | null;
  contact_email?: string | null;
  contact_phone?: string | null;
  website?: string | null;
  coverage_regions?: string[];
  service_types?: string[];
  status?: string;
  user_id?: number | null;
  linked_username?: string | null;
  linked_user_email?: string | null;
  notes?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ShipmentEvent {
  id: number;
  order_id: number;
  status: string;
  description?: string;
  location?: string;
  timestamp: string;
  logistics_partner?: string;
}

export interface OrderTrackingEvent {
  id: number;
  shipment_id: number;
  order_id: number;
  supplier_id: number;
  actor_user_id?: number | null;
  actor_role: string;
  event_type: string;
  event_label?: string | null;
  status_after?: string | null;
  distribution_channel?: string | null;
  location?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  scan_code?: string | null;
  notes?: string | null;
  created_at?: string | null;
}

export interface OrderTrackingStep {
  key: "placed" | "preparing" | "picked_up" | "in_transit" | "delivered";
  label: string;
  completed: boolean;
  active: boolean;
  timestamp?: string | null;
  notes?: string | null;
}

export interface OrderTrackingReturnSummary {
  id: number;
  order_item_id?: number | null;
  intent: "return" | "replacement";
  status: string;
  reason: string;
  resolution_notes?: string | null;
  items?: Array<{ order_item_id?: number | null; product_id: number; product_name: string; quantity: number; price: number; return_window_days?: number | null }>;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface OrderTrackingReturnEligibilityItem {
  order_item_id?: number | null;
  product_id: number;
  product_name: string;
  quantity: number;
  price: number;
  supplier_id?: number | null;
  return_window_days: number;
}

export interface OrderTrackingReturnEligibility {
  eligible: boolean;
  delivered_at?: string | null;
  return_window_days: number;
  deadline?: string | null;
  days_remaining?: number | null;
  items: OrderTrackingReturnEligibilityItem[];
}

export interface OrderTrackingRefundFinancialSummary {
  id: number;
  status: string;
  refund_reason: string;
  refund_method: string;
  customer_refund_amount: number;
  supplier_reversal: number;
  logistics_reversal: number;
  commission_reversal: number;
  vat_adjustment: number;
  created_at?: string | null;
  processed_at?: string | null;
}

export interface OrderTrackingAllocation {
  supplier_id: number;
  supplier_name?: string | null;
  partner_id?: number | null;
  partner_name?: string | null;
  partner_code?: string | null;
  service_area_id?: number | null;
  service_area_label?: string | null;
  allocation_source?: string | null;
  destination_country?: string | null;
  destination_city?: string | null;
  shipping_amount: number;
  pickup_charge: number;
  dropoff_charge: number;
  estimated_delivery_min?: number | null;
  estimated_delivery_max?: number | null;
  currency: string;
}

export interface OrderTrackingFinanceBreakdown {
  payment_method?: string | null;
  subtotal_amount: number;
  discount_amount: number;
  shipping_amount: number;
  vat_amount: number;
  service_fee_amount: number;
  total_amount: number;
  selected_partner_id?: number | null;
  selected_service_area_id?: number | null;
  estimated_delivery_min?: number | null;
  estimated_delivery_max?: number | null;
  allocations: OrderTrackingAllocation[];
  refund?: OrderTrackingRefundFinancialSummary | null;
}

export interface ShipmentConfirmationRequest {
  id: number;
  shipment_id: number;
  order_id: number;
  supplier_id: number;
  requester_user_id?: number | null;
  requester_role?: string | null;
  target_user_id?: number | null;
  target_role?: string | null;
  confirmation_type: "pickup" | "delivery";
  confirmation_type_label?: string | null;
  status: "pending" | "accepted" | "rejected" | "cancelled";
  requested_status: string;
  requested_event_type?: string | null;
  current_hub?: string | null;
  tracking_number?: string | null;
  delivery_signature_name?: string | null;
  delivery_signature_data_url?: string | null;
  notes?: string | null;
  response_notes?: string | null;
  created_at?: string | null;
  responded_at?: string | null;
}

export interface ShipmentConfirmationCreatePayload {
  requested_status: "shipped" | "delivered";
  current_hub?: string;
  tracking_number?: string;
  scan_code?: string;
  event_type?: string;
  notes?: string;
  delivery_signature_name?: string;
  delivery_signature_data_url?: string;
}

export interface ShipmentConfirmationRespondPayload {
  decision: "accepted" | "rejected";
  response_notes?: string;
}

export interface OrderTrackingShipment {
  id: number;
  order_id: number;
  supplier_id: number;
  supplier_name?: string | null;
  assigned_partner_id?: number | null;
  assigned_partner_name?: string | null;
  assigned_partner_code?: string | null;
  carrier_id?: number | null;
  carrier_name?: string | null;
  tracking_number?: string | null;
  tracking_url?: string | null;
  status: string;
  status_label?: string | null;
  distribution_channel?: string | null;
  current_hub?: string | null;
  scan_code?: string | null;
  package_count?: number | null;
  package_weight_kg?: number | null;
  package_dimensions?: string | null;
  packaged_at?: string | null;
  packaged_by_user_id?: number | null;
  packaging_notes?: string | null;
  shipping_address?: string | null;
  shipped_at?: string | null;
  estimated_delivery?: string | null;
  actual_delivery?: string | null;
  delivery_signature_name?: string | null;
  delivery_signature_data_url?: string | null;
  delivery_signature_captured_at?: string | null;
  notes?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  active_confirmation_request?: ShipmentConfirmationRequest | null;
  recent_confirmation_requests?: ShipmentConfirmationRequest[] | null;
  events?: OrderTrackingEvent[] | null;
}

export interface OrderTracking {
  order_id: number;
  order_status: string;
  order_status_label?: string | null;
  payment_method?: string | null;
  subtotal_amount?: number;
  discount_amount?: number;
  shipping_amount?: number;
  vat_amount?: number;
  total_amount?: number;
  finance_breakdown?: OrderTrackingFinanceBreakdown | null;
  shipment_count: number;
  delivered_shipments: number;
  pending_shipments: number;
  all_shipments_delivered: boolean;
  tracking_numbers: string[];
  available_scan_codes: string[];
  shipping_address?: string | null;
  customer_phone?: string | null;
  delivery_location?: string | null;
  delivery_note?: string | null;
  return_eligibility?: OrderTrackingReturnEligibility | null;
  active_return_request?: OrderTrackingReturnSummary | null;
  items: Array<{
    order_item_id?: number | null;
    product_id: number;
    product_name: string;
    quantity: number;
    price: number;
    supplier_id?: number | null;
    return_window_days?: number | null;
  }>;
  timeline: OrderTrackingStep[];
  shipments: OrderTrackingShipment[];
}

export interface SupplierLabelPayload {
  order_id: number;
  shipment_id: number | null;
  has_shipment: boolean;
  sheet_mode: "packing" | "shipment";
  invoice_number: string;
  order_status: string;
  shipment_status: string;
  shipment_status_label?: string | null;
  ordered_at?: string | null;
  paid_at?: string | null;
  payment_method?: string | null;
  supplier_name?: string | null;
  supplier_email?: string | null;
  supplier_phone?: string | null;
  supplier_address?: string | null;
  supplier_website?: string | null;
  supplier_tax_id?: string | null;
  supplier_logo_url?: string | null;
  customer_name: string;
  customer_email?: string | null;
  customer_phone?: string | null;
  shipping_address?: string | null;
  delivery_location?: string | null;
  delivery_note?: string | null;
  carrier_name?: string | null;
  tracking_number?: string | null;
  scan_code: string;
  current_hub?: string | null;
  package_count?: number | null;
  package_weight_kg?: number | null;
  package_dimensions?: string | null;
  packaged_at?: string | null;
  packaging_notes?: string | null;
  subtotal: number;
  discount?: number;
  vat: number;
  shipping: number;
  total: number;
  items: Array<{
    order_item_id?: number;
    product_id: number;
    product_name: string;
    quantity: number;
    unit_price: number;
    line_total: number;
  }>;
}

export interface ProductVerification {
  id: number;
  product_id: number;
  product_name?: string;
  supplier_id: number;
  barcode?: string;
  qr_code?: string;
  status: "pending" | "verified" | "failed";
  notes?: string;
  verified_at?: string;
  created_at: string;
}

export interface AdminAnalytics {
  total_revenue: number;
  total_orders: number;
  total_users: number;
  total_products: number;
  active_suppliers: number;
  pending_returns: number;
  revenue_growth?: number;
  orders_growth?: number;
  users_growth?: number;
}

// ── Customer-facing Supplier interfaces ──────────────────────────────────────

export interface SupplierCertification {
  title: string;
  issuer?: string;
  year?: number;
  image_url?: string;
}

export interface SupplierSocialLinks {
  instagram?: string;
  facebook?: string;
  twitter?: string;
  linkedin?: string;
  youtube?: string;
  tiktok?: string;
}

export interface SupplierPublicReview {
  id: number;
  rating: number;
  comment?: string | null;
  username?: string;
  customer_name?: string;
  product_name?: string;
  created_at: string;
  is_verified_purchase?: boolean;
}

export interface SupplierPublicProfile {
  id: number;
  username: string;
  slug: string;
  business_name?: string | null;
  business_type: string;
  country?: string | null;
  region?: string | null;
  city?: string | null;
  website?: string | null;
  bio?: string | null;
  about_us?: string | null;
  logo_url?: string | null;
  banner_url?: string | null;
  video_url?: string | null;
  certifications: SupplierCertification[];
  social_links: SupplierSocialLinks;
  established_year?: number | null;
  verification_status: string;
  badge_level: string;
  credibility_score: number;
  member_since: string;
  is_verified: boolean;
  product_count: number;
  avg_rating: number;
  total_reviews: number;
  total_sales: number;
  recent_reviews?: SupplierPublicReview[];
}

export interface SupplierPublicSummary {
  id: number;
  username: string;
  slug: string;
  business_name?: string | null;
  country?: string | null;
  city?: string | null;
  logo_url?: string | null;
  bio?: string | null;
  badge_level: string;
  verification_status: string;
  credibility_score: number;
  is_verified: boolean;
  product_count: number;
  avg_rating: number;
  total_reviews: number;
  total_sales: number;
  member_since: string;
}

export interface ProductVideo {
  id: number;
  product_id: number;
  video_url: string;
  thumbnail_url?: string;
  duration_seconds?: number;
  video_type?: string;
  title?: string;
  description?: string;
  views_count: number;
  is_featured: boolean;
  upload_status: string;
  created_at?: string;
  product_name?: string;
  product_price?: number | null;
}

// ── Admin Hierarchy & Approval Matrix ──────────────────────────────────────

export interface OrgUnit {
  id: number;
  name: string;
  parent_id?: number | null;
  path?: string | null;
  is_active: boolean;
}

export interface EmployeeRecord {
  id: number;
  user_id: number;
  username?: string;
  email?: string;
  full_name?: string;
  role?: string;
  org_unit_id?: number | null;
  org_unit_name?: string | null;
  authority_level?: number | null;
  reporting_manager_id?: number | null;
  manager_name?: string | null;
  department?: string | null;
  job_title?: string | null;
}

export interface HierarchyChainNode {
  user_id: number;
  username: string;
  role: string;
  authority_level?: number | null;
  org_unit_name?: string | null;
}

export interface ApprovalRuleSummary {
  label: string;
  min_authority_level: number;
  department?: string | null;
  org_unit_required: boolean;
  description: string;
}

export interface ApprovalMatrixRules {
  rules: Record<string, ApprovalRuleSummary>;
}

export interface ApprovalEligibility {
  can_approve: boolean;
  user_id: number;
  resource_type: string;
  authority_level?: number | null;
  amount?: number | null;
  reason?: string;
}

export interface ApproverSummary {
  user_id: number;
  username: string;
  role: string;
  authority_level: number;
  org_unit_name?: string | null;
  department?: string | null;
  distance?: number;
}

export interface ApprovalChainItem {
  user_id: number;
  username: string;
  role: string;
  authority_level: number;
  org_unit_name?: string | null;
  distance: number;
}

export interface ApprovalMatrixResponse {
  resource_type: string;
  org_unit_id?: number | null;
  approvers: ApproverSummary[];
  count: number;
}

export interface ApprovalChainResponse {
  user_id: number;
  resource_type: string;
  chain: ApprovalChainItem[];
  count: number;
}

export interface AdminPayoutRecord {
  id: number;
  supplier_id: number;
  supplier_name?: string;
  amount: number;
  currency?: string;
  status: string;
  method?: string;
  reference?: string;
  notes?: string;
  created_at: string;
  processed_at?: string;
  verification_note?: string | null;
  approved_by?: number | null;
  approved_by_name?: string | null;
}

export interface AdminProductRecord {
  id: number;
  name: string;
  category: string;
  price: number | null;
  supplier_id?: number;
  supplier_name?: string;
  moderation_status?: string;
  is_verified?: boolean;
  stock: number;
  created_at?: string;
}

export interface AdminSupplierRecord {
  id: number;
  username: string;
  email: string;
  business_name?: string;
  verification_status?: string;
  is_verified?: boolean;
  badge_level?: string;
  credibility_score?: number;
  product_count?: number;
  order_count?: number;
  revenue?: number;
  created_at?: string;
}
