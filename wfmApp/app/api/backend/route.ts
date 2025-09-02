import { NextRequest, NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_BPMN_BACKEND_URL || 'http://localhost:8100';

async function proxyRequest(path: string, req: NextRequest) {
  const target = `${API_BASE}${path}`;

  // Build fetch options mirroring the incoming request
  const init: RequestInit = {
    method: req.method,
    headers: {
      // Forward content-type if present; allow backend to handle other headers
      ...(req.headers.get('content-type') ? { 'Content-Type': req.headers.get('content-type')! } : {}),
      'User-Agent': 'wfm-unified-proxy/1.0',
    },
    // Don't forward cookies by default
    credentials: 'omit'
  };

  // Copy body for methods that usually have one
  if (req.method && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(req.method.toUpperCase())) {
    try {
      init.body = await req.text();
    } catch (e) {
      // ignore
    }
  }

  const response = await fetch(target, init);

  const respText = await response.text();

  const headers: Record<string, string> = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,PATCH,DELETE,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
  };

  // Try to mirror content-type when possible
  const contentType = response.headers.get('content-type');
  if (contentType) headers['Content-Type'] = contentType;

  return new NextResponse(respText, { status: response.status, headers });
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const path = searchParams.get('path');
    if (!path) {
      return NextResponse.json({ error: 'Missing path parameter' }, { status: 400 });
    }
    return await proxyRequest(path, request);
  } catch (err) {
    return NextResponse.json({ error: 'Proxy GET failed', details: err instanceof Error ? err.message : String(err) }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const path = searchParams.get('path');
    if (!path) {
      return NextResponse.json({ error: 'Missing path parameter' }, { status: 400 });
    }
    return await proxyRequest(path, request);
  } catch (err) {
    return NextResponse.json({ error: 'Proxy POST failed', details: err instanceof Error ? err.message : String(err) }, { status: 500 });
  }
}

export async function PUT(request: NextRequest) {
  return POST(request);
}

export async function DELETE(request: NextRequest) {
  return POST(request);
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET,POST,PUT,PATCH,DELETE,OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    },
  });
}
