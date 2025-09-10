// Reusable CORS helper to centralize logic based on environment flags
import { NextRequest, NextResponse } from 'next/server';

interface CorsConfig {
  enableAll: boolean;
  allowAny: boolean;
  dynamicOrigin: boolean;
  allowCredentials: boolean;
  allowedOrigins: string[];
  allowedHeaders: string[];
  exposeHeaders: string[];
  extraMethods: string[];
}

function getEnvFlag(name: string, def: string | undefined = undefined): string | undefined {
  if (typeof process.env[name] === 'string') return process.env[name];
  return def;
}

function parseBool(val: string | undefined): boolean {
  if (!val) return false;
  return ['1', 'true', 'yes', 'on'].includes(val.toLowerCase());
}

export function readCorsConfig(): CorsConfig {
  return {
    enableAll: parseBool(getEnvFlag('CORS_ENABLE_ALL', 'true')), // default true for dev
    allowAny: parseBool(getEnvFlag('CORS_ALLOW_ANY_ORIGIN', 'true')),
    dynamicOrigin: parseBool(getEnvFlag('CORS_DYNAMIC_ORIGIN', 'true')),
    allowCredentials: parseBool(getEnvFlag('CORS_ALLOW_CREDENTIALS', 'false')),
    allowedOrigins: (getEnvFlag('CORS_ALLOWED_ORIGINS', '') || '')
      .split(',')
      .map(o => o.trim())
      .filter(Boolean),
    allowedHeaders: (getEnvFlag('CORS_ALLOWED_HEADERS', 'Content-Type,Authorization') || '')
      .split(',')
      .map(h => h.trim())
      .filter(Boolean),
    exposeHeaders: (getEnvFlag('CORS_EXPOSE_HEADERS', 'Content-Length,Content-Type') || '')
      .split(',')
      .map(h => h.trim())
      .filter(Boolean),
    extraMethods: (getEnvFlag('CORS_EXTRA_METHODS', '') || '')
      .split(',')
      .map(m => m.trim().toUpperCase())
      .filter(Boolean),
  };
}

export function buildCorsHeaders(req?: NextRequest): Record<string, string> {
  const cfg = readCorsConfig();
  if (!cfg.enableAll) return {};

  const baseMethods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'];
  const methods = Array.from(new Set([...baseMethods, ...cfg.extraMethods])).join(',');

  let origin = '*';
  if (!cfg.allowAny) {
    if (cfg.dynamicOrigin) {
      const reqOrigin = req?.headers.get('origin');
      if (reqOrigin) {
        if (cfg.allowedOrigins.length === 0 || cfg.allowedOrigins.includes(reqOrigin)) {
          origin = reqOrigin;
        }
      }
    } else if (cfg.allowedOrigins.length > 0) {
      origin = cfg.allowedOrigins[0];
    }
  }

  const headers: Record<string, string> = {
    'Access-Control-Allow-Origin': origin,
    'Access-Control-Allow-Methods': methods,
    'Access-Control-Allow-Headers': cfg.allowedHeaders.join(',') || 'Content-Type,Authorization',
    'Access-Control-Expose-Headers': cfg.exposeHeaders.join(','),
  };

  if (cfg.allowCredentials && origin !== '*') {
    headers['Access-Control-Allow-Credentials'] = 'true';
  }

  return headers;
}

export function withCors(response: NextResponse, req?: NextRequest) {
  const corsHeaders = buildCorsHeaders(req);
  Object.entries(corsHeaders).forEach(([k, v]) => {
    if (v) response.headers.set(k, v);
  });
  return response;
}

export function preflight(req: NextRequest) {
  const res = new NextResponse(null, { status: 200 });
  return withCors(res, req);
}
