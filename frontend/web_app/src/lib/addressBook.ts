export interface DeliveryDetails {
  fullName: string;
  phone: string;
  street: string;
  city: string;
  zip: string;
  country: string;
  deliveryLocation: string;
  deliveryNote: string;
}

export const EMPTY_DELIVERY_DETAILS: DeliveryDetails = {
  fullName: "",
  phone: "",
  street: "",
  city: "",
  zip: "",
  country: "",
  deliveryLocation: "",
  deliveryNote: "",
};

export function parseAddressBook(addressBook?: string | null): DeliveryDetails {
  if (!addressBook) return { ...EMPTY_DELIVERY_DETAILS };
  try {
    const parsed = JSON.parse(addressBook);
    const source = Array.isArray(parsed)
      ? parsed.find((item) => item?.is_default) || parsed[0]
      : parsed?.default_shipping || parsed;
    if (!source || typeof source !== "object") return { ...EMPTY_DELIVERY_DETAILS };
    return {
      fullName: source.full_name || source.fullName || "",
      phone: source.phone || "",
      street: source.street || "",
      city: source.city || "",
      zip: source.zip || source.postal_code || "",
      country: source.country || "",
      deliveryLocation: source.delivery_location || source.deliveryLocation || "",
      deliveryNote: source.delivery_note || source.deliveryNote || "",
    };
  } catch {
    return { ...EMPTY_DELIVERY_DETAILS };
  }
}

export function stringifyAddressBook(details: DeliveryDetails): string {
  return JSON.stringify({
    default_shipping: {
      full_name: details.fullName,
      phone: details.phone,
      street: details.street,
      city: details.city,
      zip: details.zip,
      country: details.country,
      delivery_location: details.deliveryLocation,
      delivery_note: details.deliveryNote,
      shipping_address: [details.fullName, details.street, details.city, details.zip, details.country]
        .filter(Boolean)
        .join(", "),
    },
  });
}
