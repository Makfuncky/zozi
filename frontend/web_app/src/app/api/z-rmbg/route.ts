import { NextRequest, NextResponse } from "next/server";

const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

async function streamToArrayBuffer(stream: ReadableStream<Uint8Array>): Promise<ArrayBuffer> {
  const reader = stream.getReader();
  const chunks: Uint8Array[] = [];
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
  }
  const total = chunks.reduce((s, c) => s + c.length, 0);
  const result = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    result.set(chunk, offset);
    offset += chunk.length;
  }
  return result.buffer;
}

export async function POST(request: NextRequest) {
  try {
    const target = request.nextUrl.searchParams.get("target");
    if (!target) {
      return NextResponse.json({ detail: "Missing target query param" }, { status: 400 });
    }

    const contentType = request.headers.get("content-type") || "";

    const backendHeaders: Record<string, string> = {
      "Content-Type": contentType,
    };

    const fwd = ["authorization", "x-csrf-token", "x-country-code", "cookie"];
    for (const h of fwd) {
      const val = request.headers.get(h);
      if (val) backendHeaders[h] = val;
    }

    if (!request.body) {
      return NextResponse.json({ detail: "No request body" }, { status: 400 });
    }

    const body = await streamToArrayBuffer(request.body);

    const backendResponse = await fetch(`${API_URL}${target}`, {
      method: "POST",
      headers: backendHeaders,
      body: body,
    });

    const respBody = await backendResponse.arrayBuffer();
    const respContentType = backendResponse.headers.get("Content-Type") || "application/octet-stream";

    return new NextResponse(respBody, {
      status: backendResponse.status,
      headers: {
        "Content-Type": respContentType,
        "Cache-Control": "no-store",
      },
    });
  } catch (error) {
    console.error("[z-rmbg] error:", error);
    return NextResponse.json({ detail: "Proxy failed: " + (error instanceof Error ? error.message : String(error)) }, { status: 500 });
  }
}

export const runtime = "nodejs";
