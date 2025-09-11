import { NextRequest, NextResponse } from 'next/server';
import { withCors, preflight } from '@/lib/cors';
import { promises as fs } from 'fs';
import path from 'path';

interface ConflictAuditRecord {
  timestamp: number;
  filename: string;
  action: string;
  diff?: any;
  sessionId?: string;
}

// In-memory cache + file persistence (best-effort, not for high concurrency)
const auditStore: ConflictAuditRecord[] = [];
const AUDIT_DIR = process.env.AUDIT_LOG_DIR || path.join(process.cwd(), 'tmp');
const AUDIT_FILE = path.join(AUDIT_DIR, 'conflict-audit.json');

async function ensureLoaded() {
  if (auditStore.length > 0) return; // already loaded
  try {
    await fs.mkdir(AUDIT_DIR, { recursive: true });
    const buf = await fs.readFile(AUDIT_FILE, 'utf-8');
    const data = JSON.parse(buf);
    if (Array.isArray(data)) {
      data.forEach(d => auditStore.push(d));
    }
  } catch { /* ignore */ }
}

async function persist() {
  try {
    await fs.mkdir(AUDIT_DIR, { recursive: true });
    // Simple rotation if file grows large
    if (auditStore.length > 500) auditStore.splice(0, auditStore.length - 500);
    await fs.writeFile(AUDIT_FILE, JSON.stringify(auditStore, null, 2), 'utf-8');
  } catch { /* ignore */ }
}

export async function POST(request: NextRequest) {
  try {
    await ensureLoaded();
    const body = await request.json();
    const rec: ConflictAuditRecord = {
      timestamp: Date.now(),
      filename: body.filename,
      action: body.action,
      diff: body.diff,
      sessionId: body.sessionId,
    };
    auditStore.push(rec);
    // Trim to last 200
    if (auditStore.length > 200) auditStore.splice(0, auditStore.length - 200);
    persist();
    return withCors(NextResponse.json({ success: true }), request);
  } catch (e) {
    return NextResponse.json({ success: false, error: 'Failed to log audit' }, { status: 500 });
  }
}

export async function GET(request: NextRequest) {
  await ensureLoaded();
  return withCors(NextResponse.json({ success: true, data: auditStore.slice().reverse() }), request);
}

export async function OPTIONS(request: NextRequest) { return preflight(request); }
