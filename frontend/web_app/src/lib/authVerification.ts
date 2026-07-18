import { apiFetch, getErrorMessage, parseJsonResponse } from "@/lib/api";

const EMAIL_VERIFICATION_REQUIRED_RE = /email(?: address)? not verified|verify your email/i;
const GENERIC_RESEND_SUCCESS =
  "If an unverified account exists for that email or username, a verification email has been sent.";

export function isEmailVerificationRequired(message: string): boolean {
  return EMAIL_VERIFICATION_REQUIRED_RE.test(message);
}

export async function resendVerificationEmail(identifier: string): Promise<string> {
  const res = await apiFetch("/auth/resend-verification/public", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ identifier }),
    skipAuthRedirect: true,
  });

  const data = await parseJsonResponse(res);
  if (!res.ok) {
    throw new Error(getErrorMessage(data || {}));
  }

  return data?.detail || GENERIC_RESEND_SUCCESS;
}
