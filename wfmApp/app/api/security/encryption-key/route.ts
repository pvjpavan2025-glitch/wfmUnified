import { NextRequest, NextResponse } from 'next/server';
import { withCors, preflight } from '@/lib/cors';

// In-memory cached symmetric key JWK (ephemeral per server restart)
let cachedKey: JsonWebKey | null = null;

async function generateKey(): Promise<JsonWebKey> {
  const key = await crypto.subtle.generateKey({ name: 'AES-GCM', length: 256 }, true, ['encrypt', 'decrypt']);
  const jwk = await crypto.subtle.exportKey('jwk', key);
  // Scrub unnecessary fields
  return jwk;
}

export async function GET(request: NextRequest) {
  try {
    if (!cachedKey) {
      cachedKey = await generateKey();
    }
    return withCors(NextResponse.json({ success: true, key: cachedKey }), request);
  } catch (e) {
    return NextResponse.json({ success: false, error: 'Failed to generate key' }, { status: 500 });
  }
}

export async function OPTIONS(request: NextRequest) { return preflight(request); }
