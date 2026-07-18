import { NextRequest, NextResponse } from "next/server";
import { applyBackendSetCookies } from "../_shared/cookies";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    const response = await fetch(`${BACKEND_URL}/auth/logout`, {
      method: "POST",
      headers: {
        cookie: request.headers.get("cookie") || "",
      },
      cache: "no-store",
    });

    const text = await response.text();
    const nextResponse = new NextResponse(text, {
      status: response.status,
      headers: {
        "Content-Type": response.headers.get("content-type") || "application/json",
      },
    });
    applyBackendSetCookies(nextResponse, response.headers);
    return nextResponse;
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the backend service" },
      { status: 502 }
    );
  }
}
