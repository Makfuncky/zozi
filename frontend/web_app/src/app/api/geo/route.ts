import { NextRequest, NextResponse } from "next/server";

function extractClientIp(request: NextRequest): string | null {
  const forwardedFor = request.headers.get("x-forwarded-for");
  if (forwardedFor) {
    const first = forwardedFor.split(",")[0]?.trim();
    if (first) return first;
  }

  const realIp = request.headers.get("x-real-ip")?.trim();
  if (realIp) return realIp;

  return null;
}

function countryFromHeaders(request: NextRequest): string | null {
  const directCountry =
    request.headers.get("x-vercel-ip-country") ||
    request.headers.get("cf-ipcountry") ||
    request.headers.get("x-country-code");
  if (directCountry && /^[A-Za-z]{2}$/.test(directCountry)) {
    return directCountry.toUpperCase();
  }

  const language = request.headers.get("accept-language")?.toLowerCase() || "";
  if (language.includes("-pk") || language.includes("ur-pk")) return "PK";
  if (language.includes("-om") || language.includes("ar-om")) return "OM";
  if (language.includes("-ae") || language.includes("ar-ae")) return "AE";

  return null;
}

export async function GET(request: NextRequest) {
  const fallbackCountry = countryFromHeaders(request);
  const clientIp = extractClientIp(request);
  const geoUrl = clientIp ? `https://ipapi.co/${encodeURIComponent(clientIp)}/json/` : "https://ipapi.co/json/";
  try {
    const response = await fetch(geoUrl, {
      headers: {
        Accept: "application/json",
      },
      cache: "no-store",
    });

    if (!response.ok) {
      return NextResponse.json({ country_code: fallbackCountry }, { status: 200 });
    }

    const data = await response.json();
    return NextResponse.json({ country_code: data.country_code ?? fallbackCountry ?? null }, { status: 200 });
  } catch {
    return NextResponse.json({ country_code: fallbackCountry }, { status: 200 });
  }
}
