import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";
import { normalizeCountryCode } from "@shared/localization";

const COUNTRY_STORAGE_KEY = "zozi_selected_country";

let inMemoryCountryCode: string | null = null;

export function setInMemorySelectedCountryCode(countryCode?: string | null) {
  inMemoryCountryCode = normalizeCountryCode(countryCode) || null;
}

export function getInMemorySelectedCountryCode(): string | null {
  return inMemoryCountryCode;
}

export async function getPersistedSelectedCountryCode(): Promise<string | null> {
  if (inMemoryCountryCode) {
    return inMemoryCountryCode;
  }

  try {
    const raw = Platform.OS === "web"
      ? globalThis.localStorage?.getItem(COUNTRY_STORAGE_KEY) ?? null
      : await SecureStore.getItemAsync(COUNTRY_STORAGE_KEY);
    const normalized = normalizeCountryCode(raw);
    inMemoryCountryCode = normalized || null;
    return inMemoryCountryCode;
  } catch {
    return null;
  }
}

export async function persistSelectedCountryCode(countryCode?: string | null): Promise<void> {
  const normalized = normalizeCountryCode(countryCode);
  inMemoryCountryCode = normalized || null;

  if (Platform.OS === "web") {
    if (normalized) {
      globalThis.localStorage?.setItem(COUNTRY_STORAGE_KEY, normalized);
    } else {
      globalThis.localStorage?.removeItem(COUNTRY_STORAGE_KEY);
    }
    return;
  }

  if (normalized) {
    await SecureStore.setItemAsync(COUNTRY_STORAGE_KEY, normalized);
  } else {
    await SecureStore.deleteItemAsync(COUNTRY_STORAGE_KEY);
  }
}

export function __resetCountrySelectionState() {
  inMemoryCountryCode = null;
}