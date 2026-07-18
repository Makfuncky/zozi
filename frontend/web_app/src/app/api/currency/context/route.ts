import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const FALLBACK_CONTEXT = {
  currency: "OMR",
  currency_code: "OMR",
  symbol: "OMR",
  name: "Omani Rial",
  locale: "en-OM",
  decimals: 3,
  country: null,
  rate_from_aed: 0.10489,
  source: "fallback",
};

export async function GET(request: NextRequest) {
  try {
    const backendUrl = new URL(`${API_URL.replace(/\/$/, "")}/currency/context`);
    request.nextUrl.searchParams.forEach((value, key) => {
      if (value) backendUrl.searchParams.set(key, value);
    });

    const response = await fetch(backendUrl.toString(), {
      headers: { Accept: "application/json" },
      cache: "no-store",
    });

    if (!response.ok) {
      return NextResponse.json(FALLBACK_CONTEXT, { status: 200 });
    }

    const data = await response.json();
    return NextResponse.json({ ...FALLBACK_CONTEXT, ...data }, { status: 200 });
  } catch {
    return NextResponse.json(FALLBACK_CONTEXT, { status: 200 });
  }
}
