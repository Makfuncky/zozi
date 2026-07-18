"use client";

import { create } from "zustand";
import { DeliveryDetails, EMPTY_DELIVERY_DETAILS, parseAddressBook } from "./addressBook";
import { useCurrencyStore } from "./currencyStore";

const STORAGE_KEY = "zozi_delivery_details";

function persist(details: DeliveryDetails) {
  if (typeof window !== "undefined") {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(details));
  }
}

function hydrate(): DeliveryDetails {
  if (typeof window === "undefined") return { ...EMPTY_DELIVERY_DETAILS };
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? { ...EMPTY_DELIVERY_DETAILS, ...JSON.parse(raw) } : { ...EMPTY_DELIVERY_DETAILS };
  } catch {
    return { ...EMPTY_DELIVERY_DETAILS };
  }
}

interface DeliveryState {
  details: DeliveryDetails;
  initialize: () => void;
  updateField: (field: keyof DeliveryDetails, value: string) => void;
  setDetails: (details: Partial<DeliveryDetails>) => void;
  hydrateFromAddressBook: (addressBook?: string | null, force?: boolean) => void;
  reset: () => void;
}

export const useDeliveryStore = create<DeliveryState>((set, get) => ({
  details: { ...EMPTY_DELIVERY_DETAILS },

  initialize: () => {
    const details = hydrate();
    set({ details });
    if (details.country) {
      void useCurrencyStore.getState().setCountry(details.country);
    }
  },

  updateField: (field, value) => {
    const next = { ...get().details, [field]: value };
    persist(next);
    set({ details: next });
    if (field === "country") {
      void useCurrencyStore.getState().setCountry(value);
    }
  },

  setDetails: (details) => {
    const next = { ...get().details, ...details };
    persist(next);
    set({ details: next });
    if (details.country) {
      void useCurrencyStore.getState().setCountry(details.country);
    }
  },

  hydrateFromAddressBook: (addressBook, force = false) => {
    const current = get().details;
    const hasCurrentData = Object.entries(current).some(([key, value]) => key !== "country" && value);
    if (hasCurrentData && !force) return;
    const next = parseAddressBook(addressBook);
    persist(next);
    set({ details: next });
    if (next.country) {
      void useCurrencyStore.getState().setCountry(next.country);
    }
  },

  reset: () => {
    localStorage.removeItem(STORAGE_KEY);
    set({ details: { ...EMPTY_DELIVERY_DETAILS } });
    void useCurrencyStore.getState().setCountry("");
    void useCurrencyStore.getState().detectFromIP();
  },
}));
