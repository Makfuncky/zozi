import { OrderItem } from "./types";

export type DeliveryDetails = {
  fullName: string;
  phone: string;
  street: string;
  city: string;
  zip: string;
  country: string;
  deliveryLocation?: string;
  deliveryNote?: string;
};

export type CheckoutValidationResult = {
  valid: boolean;
  error?: string;
};

export function validateDeliveryDetails(details: DeliveryDetails): CheckoutValidationResult {
  const requiredFields: Array<keyof DeliveryDetails> = [
    "fullName",
    "phone",
    "street",
    "city",
    "country",
  ];

  for (const field of requiredFields) {
    if (!details[field] || !details[field].trim()) {
      return { valid: false, error: `${field.replace(/([A-Z])/g, " $1").trim()} is required.` };
    }
  }

  return { valid: true };
}

export function formatShippingAddress(details: DeliveryDetails): string {
  return [
    details.fullName,
    details.street,
    details.city,
    details.zip,
    details.country,
  ]
    .filter(Boolean)
    .map((part) => part.trim())
    .join(", ");
}

export function buildOrderPayload(options: {
  items: Array<{
    product_id: number;
    quantity: number;
    selected_size?: string;
    selected_color?: string;
  }>;
  deliveryDetails: DeliveryDetails;
  couponCode?: string;
  saveToProfile?: boolean;
  paymentMethod?: string;
  currency?: string;
  countryId?: number;
  taxBreakdown?: Record<string, unknown>;
}): Record<string, unknown> {
  const { items, deliveryDetails, couponCode, saveToProfile = true, paymentMethod = "cod", currency, countryId, taxBreakdown } = options;

  const payload: Record<string, unknown> = {
    items: items.map((item) => ({
      product_id: item.product_id,
      quantity: item.quantity,
      selected_size: item.selected_size || "",
      selected_color: item.selected_color || "",
    })),
    shipping_address: formatShippingAddress(deliveryDetails),
    full_name: deliveryDetails.fullName,
    street: deliveryDetails.street,
    city: deliveryDetails.city,
    zip: deliveryDetails.zip,
    country: deliveryDetails.country,
    customer_phone: deliveryDetails.phone,
    delivery_location: deliveryDetails.deliveryLocation || undefined,
    delivery_note: deliveryDetails.deliveryNote || undefined,
    save_to_profile: saveToProfile,
    coupon_code: couponCode ? couponCode.trim() : undefined,
    payment_method: paymentMethod,
    currency,
    country_id: countryId,
    tax_breakdown: taxBreakdown,
  };

  // Remove undefined fields for cleaner API request
  Object.keys(payload).forEach((key) => {
    if (payload[key] === undefined) {
      delete payload[key];
    }
  });

  return payload;
}

export function calculateSubtotal(items: Array<{ price: number; quantity: number }>): number {
  return items.reduce((sum, item) => sum + item.price * item.quantity, 0);
}
