import { Platform } from "react-native";

/**
 * Web fallback: expo-secure-store has no native implementation on web.
 * Use localStorage so Zustand persist still works in the browser.
 */
function getWebStorage() {
  const store: Record<string, string> = {};
  return {
    getItem: async (key: string): Promise<string | null> => {
      try {
        const v = typeof localStorage !== "undefined" ? localStorage.getItem(key) : store[key];
        return v ?? null;
      } catch {
        return store[key] ?? null;
      }
    },
    setItem: async (key: string, value: string): Promise<void> => {
      try {
        if (typeof localStorage !== "undefined") localStorage.setItem(key, value);
        else store[key] = value;
      } catch {
        store[key] = value;
      }
    },
    removeItem: async (key: string): Promise<void> => {
      try {
        if (typeof localStorage !== "undefined") localStorage.removeItem(key);
        delete store[key];
      } catch {
        delete store[key];
      }
    },
  };
}

/**
 * Expo SecureStore adapter for Zustand persistence.
 * Provides a compatible interface for createJSONStorage.
 * Falls back to localStorage on web where SecureStore is unavailable.
 */
export const ExpoSecureStorage =
  Platform.OS === "web"
    ? getWebStorage()
    : {
        getItem: async (key: string): Promise<string | null> => {
          const SecureStore = await import("expo-secure-store");
          return await SecureStore.getItemAsync(key);
        },
        setItem: async (key: string, value: string): Promise<void> => {
          const SecureStore = await import("expo-secure-store");
          await SecureStore.setItemAsync(key, value);
        },
        removeItem: async (key: string): Promise<void> => {
          const SecureStore = await import("expo-secure-store");
          await SecureStore.deleteItemAsync(key);
        },
      };

/**
 * Web-safe standalone helpers mirroring the expo-secure-store async API.
 * Use these instead of importing expo-secure-store directly so the app
 * works in the browser (where SecureStore has no native implementation).
 */
export async function secureGetItemAsync(key: string): Promise<string | null> {
  if (Platform.OS === "web") {
    try {
      return typeof localStorage !== "undefined" ? localStorage.getItem(key) : null;
    } catch {
      return null;
    }
  }
  const SecureStore = await import("expo-secure-store");
  return await SecureStore.getItemAsync(key);
}

export async function secureSetItemAsync(key: string, value: string): Promise<void> {
  if (Platform.OS === "web") {
    try {
      if (typeof localStorage !== "undefined") localStorage.setItem(key, value);
    } catch {
      /* ignore quota/availability errors */
    }
    return;
  }
  const SecureStore = await import("expo-secure-store");
  await SecureStore.setItemAsync(key, value);
}

export async function secureDeleteItemAsync(key: string): Promise<void> {
  if (Platform.OS === "web") {
    try {
      if (typeof localStorage !== "undefined") localStorage.removeItem(key);
    } catch {
      /* ignore */
    }
    return;
  }
  const SecureStore = await import("expo-secure-store");
  await SecureStore.deleteItemAsync(key);
}