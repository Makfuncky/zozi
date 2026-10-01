import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const dynamic = "force-dynamic";
export const revalidate = 0;

/**
 * Social auth callback endpoint.
 *
 * Receives the access token from the client (POST body) after a social OAuth
 * redirect, validates it with the backend, and sets httpOnly cookies instead
 * of exposing the token in the URL.
 *
 * Security: The token is never stored in localStorage or left in the URL.
 * It is exchanged server-side for httpOnly cookies.
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json().catch(() => null);
    const token: string | undefined = body?.token;

    if (!token) {
      return NextResponse.json(
        { detail: "Missing token" },
        { status: 400 }
      );
    }

    // Validate the token with the backend by attempting to use it
    const backendRes = await fetch(`${BACKEND_URL}/auth/me`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      cache: "no-store",
    });

    if (!backendRes.ok) {
      return NextResponse.json(
        { detail: "Invalid or expired token" },
        { status: 401 }
      );
    }

    const userData = await backendRes.json();

    // Create response with user data
    const nextResponse = NextResponse.json(
      { user: userData },
      { status: 200 }
    );

    // Set the access token in an httpOnly cookie
    // This is more secure than passing it in the URL
    nextResponse.cookies.set("zozi_access_token", token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/",
      maxAge: 60 * 60 * 24 * 7, // 7 days
    });

    // Also set a non-sensitive flag cookie (readable by client)
    nextResponse.cookies.set("zozi_has_session", "1", {
      httpOnly: false,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/",
      maxAge: 60 * 60 * 24 * 7, // 7 days
    });

    return nextResponse;
  } catch (error) {
    console.error("[Social Callback] Error:", error);
    return NextResponse.json(
      { detail: "Failed to process social login" },
      { status: 500 }
    );
  }
}
