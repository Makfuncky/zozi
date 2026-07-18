import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";

const COUNTRY_STORAGE_KEY = "zozi_selected_country";

const COUNTRY_ALIASES: Record<string, string> = {
  AE: "AE",
  UAE: "AE",
  UNITEDARABEMIRATES: "AE",
  EMIRATES: "AE",
  PK: "PK",
  PAKISTAN: "PK",
  OM: "OM",
  OMAN: "OM",
  SA: "SA",
  KSA: "SA",
  SAUDIARABIA: "SA",
  IN: "IN",
  INDIA: "IN",
  US: "US",
  USA: "US",
  UNITEDSTATES: "US",
  UNITEDSTATESOFAMERICA: "US",
  GB: "GB",
  UK: "GB",
  UNITEDKINGDOM: "GB",
  QA: "QA",
  QATAR: "QA",
  KW: "KW",
  KUWAIT: "KW",
  BH: "BH",
  BAHRAIN: "BH",
};

let inMemoryCountryCode: string | null = null;

export function normalizeCountryCode(raw?: string | null): string {
  const lettersOnly = String(raw || "").toUpperCase().replace(/[^A-Z]/g, "");
  if (!lettersOnly) return "";
  const aliased = COUNTRY_ALIASES[lettersOnly];
  if (aliased) return aliased;
  if (lettersOnly.length === 2) return lettersOnly;
  return "";
}

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