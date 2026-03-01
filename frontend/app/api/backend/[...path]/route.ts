/**
 * Proxy all requests to the backend. Browser calls /api/backend/... (same origin),
 * this route forwards to backend /api/... (no CORS).
 */
const BACKEND = process.env.BACKEND_URL || "http://127.0.0.1:8000";

function getBackendUrl(request: Request, pathParam: string | string[] | undefined): string {
  const segments = Array.isArray(pathParam) ? pathParam : pathParam ? [pathParam] : [];
  const path = segments.join("/");
  const backendPath = `/api/${path}`;
  const url = new URL(request.url);
  return `${BACKEND}${backendPath}${url.search}`;
}

async function getParams(context: { params: Promise<{ path?: string | string[] }> | { path?: string | string[] } }) {
  const p = context.params;
  return typeof (p as Promise<unknown>)?.then === "function" ? await (p as Promise<{ path?: string | string[] }>) : (p as { path?: string | string[] });
}

export async function GET(
  request: Request,
  context: { params: Promise<{ path?: string | string[] }> | { path?: string | string[] } }
) {
  const params = await getParams(context);
  const backendUrl = getBackendUrl(request, params?.path);
  try {
    const res = await fetch(backendUrl, {
      method: "GET",
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    const text = await res.text();
    try {
      return Response.json(JSON.parse(text), { status: res.status });
    } catch {
      return new Response(text, { status: res.status, headers: { "Content-Type": res.headers.get("Content-Type") || "text/plain" } });
    }
  } catch (err) {
    console.error("[proxy] GET error:", err);
    return Response.json(
      { error: "Backend unreachable", detail: String(err), url: backendUrl },
      { status: 503 }
    );
  }
}

export async function POST(
  request: Request,
  context: { params: Promise<{ path?: string | string[] }> | { path?: string | string[] } }
) {
  const params = await getParams(context);
  const backendUrl = getBackendUrl(request, params?.path);

  const contentType = request.headers.get("content-type") || "";
  const isFormData = contentType.includes("multipart/form-data");

  const options: RequestInit = {
    method: "POST",
    cache: "no-store",
  };

  if (isFormData) {
    options.body = await request.arrayBuffer();
    options.headers = { "Content-Type": contentType };
  } else {
    const body = await request.text();
    if (body) {
      options.body = body;
      options.headers = { "Content-Type": "application/json" };
    }
  }

  try {
    const res = await fetch(backendUrl, options);
    const text = await res.text();
    try {
      return Response.json(JSON.parse(text), { status: res.status });
    } catch {
      return new Response(text, { status: res.status, headers: { "Content-Type": res.headers.get("Content-Type") || "text/plain" } });
    }
  } catch (err) {
    console.error("[proxy] POST error:", err);
    return Response.json(
      { error: "Backend unreachable", detail: String(err), url: backendUrl },
      { status: 503 }
    );
  }
}

export async function PUT(
  request: Request,
  context: { params: Promise<{ path?: string | string[] }> | { path?: string | string[] } }
) {
  const params = await getParams(context);
  const backendUrl = getBackendUrl(request, params?.path);
  const body = await request.text();
  try {
    const res = await fetch(backendUrl, {
      method: "PUT",
      body: body || undefined,
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
    });
    const resText = await res.text();
    try {
      return Response.json(JSON.parse(resText), { status: res.status });
    } catch {
      return new Response(resText, { status: res.status });
    }
  } catch (err) {
    console.error("[proxy] PUT error:", err);
    return Response.json({ error: "Backend unreachable", detail: String(err) }, { status: 503 });
  }
}

export async function DELETE(
  request: Request,
  context: { params: Promise<{ path?: string | string[] }> | { path?: string | string[] } }
) {
  const params = await getParams(context);
  const backendUrl = getBackendUrl(request, params?.path);
  try {
    const res = await fetch(backendUrl, { method: "DELETE", cache: "no-store" });
    const text = await res.text();
    try {
      return Response.json(JSON.parse(text), { status: res.status });
    } catch {
      return new Response(text, { status: res.status });
    }
  } catch (err) {
    console.error("[proxy] DELETE error:", err);
    return Response.json({ error: "Backend unreachable", detail: String(err) }, { status: 503 });
  }
}
