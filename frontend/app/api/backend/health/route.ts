import { NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL || "http://127.0.0.1:8000";

/** Ping the real backend. Use this to show "Backend connected" or "Start the backend". */
export async function GET() {
  try {
    const res = await fetch(`${BACKEND}/`, { cache: "no-store", signal: AbortSignal.timeout(3000) });
    const ok = res.ok;
    const data = ok ? await res.json().catch(() => ({})) : {};
    return NextResponse.json({
      ok,
      backend: ok ? "connected" : "error",
      message: ok ? "Backend is running" : "Backend returned an error",
      ...data,
    });
  } catch (err) {
    return NextResponse.json(
      {
        ok: false,
        backend: "unreachable",
        message: "Backend not reachable. Start it with: cd backend && python -m uvicorn app.main:app --reload --port 8000",
        detail: String(err),
      },
      { status: 503 }
    );
  }
}
