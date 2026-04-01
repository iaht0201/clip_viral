import { NextResponse } from "next/server";

export async function GET(
  request: Request,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const upstream = await fetch(`${apiUrl}/tts/${path.join("/")}`);
  return new Response(upstream.body, { status: upstream.status, headers: upstream.headers });
}

export async function POST(
  request: Request,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const body = await request.text();
  const upstream = await fetch(`${apiUrl}/tts/${path.join("/")}`, {
    method: "POST",
    headers: { "Content-Type": request.headers.get("content-type") || "application/json" },
    body
  });
  return new Response(upstream.body, { status: upstream.status, headers: upstream.headers });
}
