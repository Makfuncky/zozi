import { NextRequest, NextResponse } from "next/server";
import { applyBackendSetCookies } from "../_shared/cookies";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    const contentType = (request.headers.get("content-type") || "").toLowerCase();
    const body = await request.text();
    const backendPath = contentType.includes("application/x-www-form-urlencoded")
      ? "/auth/login/form"
      : "/auth/login";
    const response = await fetch(`${BACKEND_URL}${backendPath}`, {
      method: "POST",
      headers: {
        "Content-Type": contentType || "application/x-www-form-urlencoded",
      },
      body,
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
