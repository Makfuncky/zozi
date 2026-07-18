import React, { useEffect, useRef } from "react";
import { LogBox, Platform } from "react-native";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { SafeAreaProvider } from "react-native-safe-area-context";
import * as SplashScreen from "expo-splash-screen";
import Constants from "expo-constants";
import { useAuthStore } from "@/lib/authStore";
import { useThemeStore } from "@/lib/themeStore";
import { setAuthExpiredCallback } from "@/lib/api";
import { setLogLevel } from "@/lib/logger";
import { ToastContainer } from "@/components/ToastContainer";
import { useRouter } from "expo-router";
import { ErrorHandlerInit } from "@/components/ui";
import ErrorBoundary from "@/components/ui/ErrorBoundary";
import { useLocaleStore } from "@/lib/localeStore";
import { useCurrencyStore } from "@/lib/currencyStore";
import { apiFetch, registerPushToken, unregisterPushToken } from "@/lib/api";
import MobileBackgroundEffect from "@/components/MobileBackgroundEffect";
import BackgroundJobCenter from "@/components/BackgroundJobCenter";
import { AuthPromptProvider } from "@/lib/authPrompt";
import { isLocale, normalizeLocale } from "@shared/localization";
import { UserRealtimeBridge } from "@/components/UserRealtimeBridge";
import * as SecureStore from "expo-secure-store";
import { CountryProvider, useCountry } from "@/lib/countryContext";

// Disable LogBox entirely to avoid React module resolution issues on Windows
LogBox.ignoreAllLogs(true);

type NotificationsModule = {
  getPermissionsAsync: () => Promise<{ status: string }>;
  requestPermissionsAsync: () => Promise<{ status: string }>;
  getExpoPushTokenAsync: (options?: { projectId?: string }) => Promise<{ data: string }>;
};

let Notifications: NotificationsModule | null = null;
try {
  Notifications = require("expo-notifications") as NotificationsModule;
} catch {
  Notifications = null;
}

const PUSH_TOKEN_STORAGE_KEY = "zozi_push_token";

async function loadStoredPushToken(): Promise<string | null> {
  if (Platform.OS === "web") {
    return globalThis.localStorage?.getItem(PUSH_TOKEN_STORAGE_KEY) ?? null;
  }

  try {
    return await SecureStore.getItemAsync(PUSH_TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

async function persistPushToken(token: string | null): Promise<void> {
  if (Platform.OS === "web") {
    if (token) {
      globalThis.localStorage?.setItem(PUSH_TOKEN_STORAGE_KEY, token);
    } else {
      globalThis.localStorage?.removeItem(PUSH_TOKEN_STORAGE_KEY);
    }
    return;
  }

  try {
    if (token) {
      await SecureStore.setItemAsync(PUSH_TOKEN_STORAGE_KEY, token);
    } else {
      await SecureStore.deleteItemAsync(PUSH_TOKEN_STORAGE_KEY);
    }
  } catch {
    // Best effort only.
  }
}

SplashScreen.preventAutoHideAsync();

// Inject brand web fonts (Fraunces + Sora) for a polished, modern look.
// Guarded so it only ever runs in a browser environment.
let fontsInjected = false;
function injectBrandFonts() {
  if (fontsInjected || typeof document === "undefined") return;
  fontsInjected = true;

  const pre1 = document.createElement("link");
  pre1.rel = "preconnect";
  pre1.href = "https://fonts.googleapis.com";
  document.head.appendChild(pre1);

  const pre2 = document.createElement("link");
  pre2.rel = "preconnect";
  pre2.href = "https://fonts.gstatic.com";
  pre2.crossOrigin = "anonymous";
  document.head.appendChild(pre2);

  const link = document.createElement("link");
  link.rel = "preload";
  link.as = "style";
  link.href =
    "https://fonts.googleapis.com/css2?family=Fraunces:wght@600;700;800;900&family=Sora:wght@400;500;600;700;800&display=swap";
  link.onload = () => {
    // Promote the preloaded stylesheet to an active one for instant application.
    link.rel = "stylesheet";
  };
  document.head.appendChild(link);

  // Also add a plain stylesheet link so the fonts apply even if onload is missed.
  const link2 = document.createElement("link");
  link2.rel = "stylesheet";
  link2.href =
    "https://fonts.googleapis.com/css2?family=Fraunces:wght@600;700;800;900&family=Sora:wght@400;500;600;700;800&display=swap";
  document.head.appendChild(link2);
}

/** Loads user's saved locale/currency preferences from the backend after login. */
function PreferencesSync() {
  const { isLoggedIn } = useAuthStore();
  const { setLocale } = useLocaleStore();
  const { setCurrency } = useCurrencyStore();
  const { setCountryCode } = useCountry();

  useEffect(() => {
    if (!isLoggedIn) return;
    apiFetch<{ preferred_language?: string; preferred_currency?: string; preferred_country?: string }>("/auth/me/preferences")
      .then((prefs) => {
        if (isLocale(prefs.preferred_language)) {
          setLocale(normalizeLocale(prefs.preferred_language));
        }
        if (prefs.preferred_country) {
          setCountryCode(prefs.preferred_country).catch(() => {});
        }
        if (prefs.preferred_currency) {
          setCurrency(prefs.preferred_currency).catch(() => {});
        }
      })
      .catch(() => {/* non-critical */});
  }, [isLoggedIn, setCountryCode, setLocale, setCurrency]);

  return null;
}

/**
 * Registers or unregisters the device's Expo push token with the backend
 * whenever the user logs in or out. Silently skips when permissions are denied.
 */
function PushTokenSync() {
  const { isLoggedIn } = useAuthStore();
  const tokenRef = useRef<string | null>(null);

  useEffect(() => {
    if (Platform.OS === "web") {
      return;
    }

    if (!Notifications) {
      return;
    }

    if (!isLoggedIn) {
      // Unregister token on logout if we have one stored
      void loadStoredPushToken().then((storedToken) => {
        const token = tokenRef.current ?? storedToken;
        if (!token) {
          return;
        }

        unregisterPushToken(token).catch(() => {});
        void persistPushToken(null);
        tokenRef.current = null;
      });
      return;
    }

    (async () => {
      try {
        const projectId = Constants.expoConfig?.extra?.eas?.projectId ?? Constants.easConfig?.projectId;

        // Request permission
        const { status: existing } = await Notifications.getPermissionsAsync();
        let finalStatus = existing;
        if (existing !== "granted") {
          const { status } = await Notifications.requestPermissionsAsync();
          finalStatus = status;
        }
        if (finalStatus !== "granted") return;

        // Get Expo push token
        const tokenData = await Notifications.getExpoPushTokenAsync(
          projectId ? { projectId } : undefined
        );
        const token = tokenData.data;
        tokenRef.current = token;

        await registerPushToken({
          token,
          platform: "expo",
          device_name: Constants.deviceName ?? Platform.OS,
        });
        await persistPushToken(token);
      } catch {
        // Non-critical — push notifications work on best-effort basis
      }
    })();
  }, [isLoggedIn]);

  return null;
}

export default function RootLayout() {
  const { initialize, isLoading } = useAuthStore();
  const { theme, mode, initTheme, initialized } = useThemeStore();
  const router = useRouter();

  // Initialize theme synchronously on web to prevent blank screen
  const isWeb = typeof window !== "undefined";
  const themeInitialized = isWeb ? true : initialized;

  useEffect(() => {
    injectBrandFonts();
    initTheme();
  }, [initTheme]);

  useEffect(() => {
    setLogLevel(__DEV__ ? "debug" : "warn");

    // Set callback for auth expiry.
    // Only bounce to the login screen if the user actually HAD a session.
    // A 401 while simply browsing unauthenticated (e.g. an optional endpoint) must
    // NOT hijack the app into the login screen — guests can tour freely.
    setAuthExpiredCallback(() => {
      const hadSession = useAuthStore.getState().isLoggedIn;
      useAuthStore.getState().logout();
      if (hadSession) {
        router.replace("/(auth)/login" as never);
      }
    });

    void initialize().finally(() => SplashScreen.hideAsync());

    // No explicit cleanup available for callback API; keep last set handler.
  }, [initialize, router]);

  // On web, don't wait for loading state (auth initializes synchronously)
  // On mobile, wait for initialization to complete
  if (!isWeb && isLoading) return null;

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      {/* Background effect — rendered behind everything (zIndex 0, pointerEvents none) */}
      <MobileBackgroundEffect />
      <SafeAreaProvider>
        <CountryProvider>
          <StatusBar style={mode === "dark" ? "light" : "dark"} />
          <ErrorHandlerInit />
          <PreferencesSync />
          <PushTokenSync />
          <UserRealtimeBridge />
          <ErrorBoundary>
            <AuthPromptProvider>
              <Stack
                screenOptions={{
                  headerStyle: { backgroundColor: theme.colors.surface1 },
                  headerTintColor: theme.colors.text,
                  headerShadowVisible: false,
                  contentStyle: { backgroundColor: theme.colors.surface0 },
                }}
              >
                <Stack.Screen name="(auth)" options={{ headerShown: false }} />
                <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
                {/* Customer screens that render their own branded <AppHeader/>.
                    Suppress the native stack header so they don't show a doubled
                    (gray native + lime AppHeader) header bar. */}
                 <Stack.Screen name="offers" options={{ headerShown: false }} />
                <Stack.Screen name="flash-sales" options={{ headerShown: false }} />
                <Stack.Screen name="settings" options={{ headerShown: false }} />
                <Stack.Screen name="help" options={{ headerShown: false }} />
                <Stack.Screen name="tickets" options={{ headerShown: false }} />
                <Stack.Screen name="ticket-detail" options={{ headerShown: false }} />
                <Stack.Screen name="referrals" options={{ headerShown: false }} />
                <Stack.Screen name="newsletter" options={{ headerShown: false }} />
                <Stack.Screen name="returns" options={{ headerShown: false }} />
                <Stack.Screen name="edit-profile" options={{ headerShown: false }} />
                <Stack.Screen name="orders" options={{ headerShown: false }} />
                <Stack.Screen
                  name="checkout"
                  options={{ title: "Checkout", presentation: "modal" }}
                />
                <Stack.Screen
                  name="wishlist"
                  options={{ headerShown: false }}
                />
                <Stack.Screen
                  name="chatbot"
                  options={{ title: "Chat", presentation: "modal" }}
                />
                <Stack.Screen
                   name="notifications"
                   options={{ headerShown: false }}
                 />
                 <Stack.Screen name="invoice" options={{ headerShown: false }} />
                 <Stack.Screen name="push-notifications" options={{ headerShown: false }} />
                 <Stack.Screen name="write-review" options={{ headerShown: false }} />
                 <Stack.Screen name="tracking/[id]" options={{ headerShown: false }} />
                 <Stack.Screen name="change-password" options={{ headerShown: false }} />
                  <Stack.Screen name="chatbot-history" options={{ headerShown: false }} />
                  <Stack.Screen name="returns/[id]" options={{ headerShown: false }} />
                 <Stack.Screen name="notification-preferences" options={{ headerShown: false }} />
                 <Stack.Screen name="archive" options={{ headerShown: false }} />
                  <Stack.Screen name="barcode-scan" options={{ headerShown: false }} />
                  <Stack.Screen name="suppliers/[id]" options={{ headerShown: false }} />
                <Stack.Screen
                  name="supplier"
                  options={{ headerShown: false }}
                />
                <Stack.Screen
                  name="logistics-partner"
                  options={{ headerShown: false }}
                />
              </Stack>
            </AuthPromptProvider>
          </ErrorBoundary>
          <BackgroundJobCenter />
          <ToastContainer />
        </CountryProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
