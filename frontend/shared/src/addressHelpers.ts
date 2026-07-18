/**
 * Shared helpers for address book management — used by both web_app and mobile_app.
 */

export interface UserAddress {
  id: number;
  user_id?: number;
  label: string;       // "Home", "Work", "Other"
  street: string;
  city: string;
  state?: string;
  zip?: string;
  country: string;
  phone?: string;
  is_default: boolean;
  created_at?: string;
}

export const ADDRESS_LABEL_OPTIONS = ["Home", "Work", "Other"] as const;
export type AddressLabel = typeof ADDRESS_LABEL_OPTIONS[number];

export function formatAddress(address: UserAddress): string {
  const parts = [address.street, address.city];
  if (address.state) parts.push(address.state);
  if (address.zip) parts.push(address.zip);
  parts.push(address.country);
  return parts.filter(Boolean).join(", ");
}

export function getDefaultAddress(addresses: UserAddress[]): UserAddress | null {
  return addresses.find((a) => a.is_default) ?? addresses[0] ?? null;
}

export function validateAddress(address: Partial<UserAddress>): string[] {
  const errors: string[] = [];
  if (!address.label?.trim()) errors.push("Label is required");
  if (!address.street?.trim()) errors.push("Street is required");
  if (!address.city?.trim()) errors.push("City is required");
  if (!address.country?.trim()) errors.push("Country is required");
  return errors;
}
