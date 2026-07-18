"use client";

import { useEffect, useRef, useState } from "react";
import { apiFetch } from "@/lib/api";

declare global {
  interface Window {
    google?: {
      accounts?: {
        id?: {
          initialize: (options: Record<string, unknown>) => void;
          renderButton: (element: HTMLElement, options: Record<string, unknown>) => void;
        };
      };
    };
  }
}

type GoogleSignInButtonProps = {
  clientId: string;
  onSuccess: (accessToken: string) => Promise<void> | void;
  onError: (message: string) => void;
};

const GOOGLE_SCRIPT_SRC = "https://accounts.google.com/gsi/client";

export default function GoogleSignInButton({ clientId, onSuccess, onError }: GoogleSignInButtonProps) {
  const buttonRef = useRef<HTMLDivElement | null>(null);
  const [scriptReady, setScriptReady] = useState(false);

  useEffect(() => {
    if (window.google?.accounts?.id) {
      setScriptReady(true);
      return;
    }

    const existingScript = document.querySelector<HTMLScriptElement>(`script[src="${GOOGLE_SCRIPT_SRC}"]`);
    if (existingScript) {
      const handleLoad = () => setScriptReady(true);
      existingScript.addEventListener("load", handleLoad);
      return () => existingScript.removeEventListener("load", handleLoad);
    }

    const script = document.createElement("script");
    script.src = GOOGLE_SCRIPT_SRC;
    script.async = true;
    script.defer = true;
    script.onload = () => setScriptReady(true);
    script.onerror = () => onError("Unable to load Google sign-in.");
    document.head.appendChild(script);

    return () => {
      script.onload = null;
      script.onerror = null;
    };
  }, [onError]);

  useEffect(() => {
    if (!scriptReady || !buttonRef.current || !window.google?.accounts?.id) {
      return;
    }

    window.google.accounts.id.initialize({
      client_id: clientId,
      callback: async (response: { credential?: string }) => {
        if (!response.credential) {
          onError("Google sign-in did not return a credential.");
          return;
        }

        try {
          const res = await apiFetch("/auth/oauth/google/id-token", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token: response.credential }),
          });
          const data = await res.json().catch(() => null);
          if (!res.ok || !data?.access_token) {
            throw new Error(data?.detail || "Google sign-in failed");
          }
          await onSuccess(data.access_token as string);
        } catch (err) {
          onError(err instanceof Error ? err.message : "Google sign-in failed");
        }
      },
      ux_mode: "popup",
    });

    buttonRef.current.innerHTML = "";
    window.google.accounts.id.renderButton(buttonRef.current, {
      theme: "outline",
      size: "large",
      width: 360,
      text: "continue_with",
      shape: "rectangular",
    });
  }, [clientId, onError, onSuccess, scriptReady]);

  return <div ref={buttonRef} className="google-signin-button min-h-11" />;
}


