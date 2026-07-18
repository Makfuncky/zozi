import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function GET(request: NextRequest) {
  try {
    const authorization = request.headers.get("authorization") || "";
    if (!authorization.trim()) {
      return NextResponse.json(
        { detail: "Missing authorization header" },
        { status: 401 }
      );
    }

    const response = await fetch(`${BACKEND_URL}/auth/me`, {
      method: "GET",
      headers: {
        authorization,
      },
      cache: "no-store",
    });

    const text = await response.text();
    return new NextResponse(text, {
      status: response.status,
      headers: {
        "Content-Type": response.headers.get("content-type") || "application/json",
      },
    });
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the backend service" },
      { status: 502 }
    );
  }
}
