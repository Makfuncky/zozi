/**
 * Payment service for mobile app.
 * Supports Tap, PayTabs, and Thawani payment gateways.
 * Note: These are SDK integration patterns - actual SDK packages need to be installed.
 */

import { apiFetch } from "@/lib/api";
import * as Linking from "expo-linking";
import { Platform } from "react-native";

export interface PaymentMethod {
  id: string;
  name: string;
  provider: "tap" | "paytabs" | "thawani";
  icon: string;
  isEnabled: boolean;
}

export interface PaymentResult {
  success: boolean;
  transactionId?: string;
  status?: string;
  error?: string;
}

// Payment configuration - should come from backend/API
const PAYMENT_CONFIG = {
  tap: {
    enabled: true,
    baseUrl: "https://app.tap.com/sdk/checkout",
  },
  paytabs: {
    enabled: true,
    baseUrl: "https://paytabs.com/paypage",
  },
  thawani: {
    enabled: true,
    baseUrl: "https://thawani.net/pay",
  },
};

/**
 * Get available payment methods
 */
export async function getPaymentMethods(): Promise<PaymentMethod[]> {
  try {
    const methods = await apiFetch<PaymentMethod[]>("/payments/methods");
    return methods;
  } catch {
    // Fallback to configured methods
    return [
      {
        id: "tap",
        name: "Tap",
        provider: "tap",
        icon: "card",
        isEnabled: PAYMENT_CONFIG.tap.enabled,
      },
      {
        id: "paytabs",
        name: "PayTabs",
        provider: "paytabs",
        icon: "card",
        isEnabled: PAYMENT_CONFIG.paytabs.enabled,
      },
      {
        id: "thawani",
        name: "Thawani",
        provider: "thawani",
        icon: "card",
        isEnabled: PAYMENT_CONFIG.thawani.enabled,
      },
    ];
  }
}

/**
 * Initialize a payment session with the backend
 */
export async function initializePaymentSession(
  orderId: number,
  methodId: string
): Promise<{
  sessionId: string;
  clientKey: string;
  paymentUrl: string;
  amount: number;
  currency: string;
}> {
  const session = await apiFetch<{
    session_id: string;
    client_key: string;
    payment_url: string;
    amount: number;
    currency: string;
  }>(`/payments/session/${orderId}`, {
    method: "POST",
    body: JSON.stringify({ method_id: methodId }),
  });

  return {
    sessionId: session.session_id,
    clientKey: session.client_key,
    paymentUrl: session.payment_url,
    amount: session.amount,
    currency: session.currency,
  };
}

/**
 * Process payment with Tap SDK
 * Requires: npm install @tap-as/sdk-react-native
 */
export async function processTapPayment(
  session: { sessionId: string; clientKey: string; paymentUrl: string; amount: number; currency: string },
  onSuccess: (result: PaymentResult) => void,
  onError: (error: string) => void
): Promise<void> {
  try {
    // Dynamic import - SDK may not be installed
    const { TapSDK } = require("@tap-as/sdk-react-native");

    const config = {
      clientKey: session.clientKey,
      environment: __DEV__ ? "sandbox" : "production",
    };

    await TapSDK.initialize(config);

    const result = await TapSDK.checkout({
      transactionId: session.sessionId,
      amount: session.amount,
      currency: session.currency,
      returnUrl: `zozi://payment/callback/${session.sessionId}`,
    });

    if (result.status === "success" || result.status === "completed") {
      onSuccess({
        success: true,
        transactionId: result.transactionId || session.sessionId,
        status: result.status,
      });
    } else {
      onError(result.errorMessage || "Payment failed");
    }
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "Tap SDK not available";
    onError(message);
  }
}

/**
 * Process payment with PayTabs SDK
 * Requires: npm install @paytabs/react-native-paytabs
 */
export async function processPayTabsPayment(
  session: { sessionId: string; clientKey: string; paymentUrl: string; amount: number; currency: string },
  onSuccess: (result: PaymentResult) => void,
  onError: (error: string) => void
): Promise<void> {
  try {
    // Dynamic import - SDK may not be installed
    const { PayTabsSDK } = require("@paytabs/react-native-paytabs");

    await PayTabsSDK.initialize({
      clientKey: session.clientKey,
      serverKey: session.clientKey, // Backend should provide this separately
      environment: __DEV__ ? "sandbox" : "production",
    });

    const result = await PayTabsSDK.startPayment({
      transactionId: session.sessionId,
      amount: session.amount,
      currency: session.currency,
      returnUrl: `zozi://payment/callback/${session.sessionId}`,
    });

    if (result.isSuccess) {
      onSuccess({
        success: true,
        transactionId: result.transactionId || session.sessionId,
        status: "completed",
      });
    } else {
      onError(result.error || "Payment failed");
    }
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "PayTabs SDK not available";
    onError(message);
  }
}

/**
 * Process payment with Thawani SDK
 * Requires: npm install @thawani/flutter-paymob@react-native (or similar)
 */
export async function processThawaniPayment(
  session: { sessionId: string; clientKey: string; paymentUrl: string; amount: number; currency: string },
  onSuccess: (result: PaymentResult) => void,
  onError: (error: string) => void
): Promise<void> {
  try {
    // Dynamic import - SDK may not be installed
    const { ThawaniSDK } = require("@thawani/rn-sdk");

    await ThawaniSDK.initialize({
      publicKey: session.clientKey,
      environment: __DEV__ ? "sandbox" : "production",
    });

    const result = await ThawaniSDK.pay({
      orderId: session.sessionId,
      amount: session.amount * 100, // Thawani uses cents
      currency: session.currency,
      callbackUrl: `zozi://payment/callback/${session.sessionId}`,
    });

    if (result.status === "success") {
      onSuccess({
        success: true,
        transactionId: result.transactionId || session.sessionId,
        status: result.status,
      });
    } else {
      onError(result.error || "Payment failed");
    }
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "Thawani SDK not available";
    onError(message);
  }
}

/**
 * Open payment URL in browser (fallback when SDK not available)
 */
export async function openPaymentUrl(url: string): Promise<void> {
  try {
    const supported = await Linking.canOpenURL(url);
    if (supported) {
      await Linking.openURL(url);
    } else {
      throw new Error("Cannot open payment URL");
    }
  } catch (error) {
    console.error("Failed to open payment URL:", error);
    throw error;
  }
}

/**
 * Verify payment status after returning from external app
 */
export async function verifyPayment(sessionId: string): Promise<PaymentResult> {
  try {
    const result = await apiFetch<PaymentResult>(`/payments/verify/${sessionId}`, {
      method: "POST",
    });
    return result;
  } catch (error) {
    const message = error instanceof Error ? error.message : "Verification failed";
    return { success: false, error: message };
  }
}

/**
 * Handle deep link callback from payment providers
 */
export function handlePaymentCallback(url: string): PaymentResult | null {
  const { path, queryParams } = Linking.parse(url);
  
  if (path?.startsWith("/payment/callback")) {
    const transactionId = queryParams?.["transaction_id"] as string;
    const status = queryParams?.["status"] as string;
    const error = queryParams?.["error"] as string;

    return {
      success: status === "success" || status === "completed",
      transactionId,
      status,
      error,
    };
  }
  
  return null;
}