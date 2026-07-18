import { NextRequest, NextResponse } from "next/server";
import { applyBackendSetCookies } from "../_shared/cookies";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function POST(request: NextRequest) {
  const cookieHeader = request.headers.get("cookie") || "";
  if (!/(?:^|;\s*)(?:zozi_refresh|refresh_token)=/.test(cookieHeader)) {
    return NextResponse.json({ access_token: null }, { status: 200 });
  }

  try {
    const response = await fetch(`${BACKEND_URL}/auth/refresh`, {
      method: "POST",
      headers: {
        cookie: cookieHeader,
      },
      cache: "no-store",
    });

    if (!response.ok) {
      return NextResponse.json({ access_token: null }, { status: 200 });
    }

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
