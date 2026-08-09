/**
 * Social sign-in helpers for the mobile app.
 *
 * The backend exposes `/auth/oauth/{google,facebook}/...` and `/auth/social/json`,
 * but OAuth providers are only usable when they are configured server-side
 * (client id + secrets). On the Expo **web** build we can use Google's
 * GSI (Google Sign-In) script when a client id is published by the backend.
 *
 * To keep the login experience polished and crash-free in every environment,
 * `socialSignIn` always returns a clear, non-fatal `SocialSignInError` when a
 * provider is unavailable instead of throwing an opaque failure. The email /
 * password flow is never blocked by social sign-in.
 */
import { Platform } from "react-native";
import { getAuthCapabilities, socialLogin, type AuthResponse } from "@/lib/api";

export type SocialProvider = "google" | "facebook" | "apple";

export const SOCIAL_PROVIDER_LABELS: Record<SocialProvider, string> = {
  google: "Google",
  facebook: "Facebook",
  apple: "Apple",
};

/** Thrown when a provider is not configured / unavailable in the current build. */
export class SocialSignInError extends Error {
  constructor(
    message: string,
    public provider: SocialProvider,
    /** True when the provider is technically available but the attempt failed. */
    public configured = false,
  ) {
    super(message);
    this.name = "SocialSignInError";
  }
}

const GOOGLE_GSI_SRC = "https://accounts.google.com/gsi/client";

type GoogleAccounts = {
  accounts?: {
    id?: {
      initialize: (options: Record<string, unknown>) => void;
      prompt?: (callback?: (notification: { getDismissedReason?: () => string }) => void) => void;
    };
  };
};

declare global {
  interface Window {
    google?: GoogleAccounts;
  }
}

function loadGoogleScript(): Promise<void> {
  if (typeof document === "undefined") return Promise.resolve();
  if (window.google?.accounts?.id) return Promise.resolve();

  return new Promise((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>(
      `script[src="${GOOGLE_GSI_SRC}"]`,
    );
    if (existing) {
      existing.addEventListener("load", () => resolve());
      existing.addEventListener("error", () => reject(new Error("Failed to load Google script")));
      return;
    }
    const script = document.createElement("script");
    script.src = GOOGLE_GSI_SRC;
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Failed to load Google script"));
    document.head.appendChild(script);
  });
}

/** Shows the Google One-Tap / popup and resolves with the id_token credential. */
function requestGoogleIdToken(clientId: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const accounts = window.google?.accounts?.id;
    if (!accounts) {
      reject(new SocialSignInError("Google sign-in is unavailable.", "google", false));
      return;
    }

    accounts.initialize({
      client_id: clientId,
      callback: (response: { credential?: string }) => {
        if (response.credential) {
          resolve(response.credential);
        } else {
          reject(new SocialSignInError("Google did not return a credential.", "google", true));
        }
      },
      ux_mode: "popup",
    });

    if (typeof accounts.prompt === "function") {
      accounts.prompt((notification) => {
        const reason = notification?.getDismissedReason?.();
        if (reason && reason !== "credential_returned") {
          reject(
            new SocialSignInError("Google sign-in was dismissed.", "google", true),
          );
        }
      });
    }
  });
}

/**
 * Attempts social sign-in for the given provider.
 * Resolves with the backend auth response on success, or rejects with a
 * `SocialSignInError` describing why the provider is unavailable.
 */
export async function socialSignIn(provider: SocialProvider): Promise<AuthResponse> {
  if (provider === "google" && Platform.OS === "web") {
    try {
      const caps = await getAuthCapabilities();
      if (caps.google && caps.google_client_id) {
        const idToken = await requestGoogleIdToken(caps.google_client_id);
        return await socialLogin({
          provider: "google",
          id_token: idToken,
          access_token: idToken,
        });
      }
    } catch (err) {
      if (err instanceof SocialSignInError) throw err;
      throw new SocialSignInError(
        "Google sign-in is not available in this environment.",
        "google",
        false,
      );
    }
  }

  // Facebook / Apple require native SDKs + server secrets that are not part of
  // this build. Surface a friendly, actionable message rather than crashing.
  throw new SocialSignInError(
    `${SOCIAL_PROVIDER_LABELS[provider]} sign-in isn't available in this environment yet. Continue with your email.`,
    provider,
    false,
  );
}
