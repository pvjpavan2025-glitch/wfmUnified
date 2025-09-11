import { NextRequest, NextResponse } from 'next/server';
import { withCors, preflight } from '@/lib/cors';
<<<<<<< HEAD
import crypto from 'crypto';
=======
>>>>>>> 9f492dd7a98e4a8bb5157fa332edc8af17e007ea
import { promises as fs } from 'fs';
import path from 'path';

interface ConflictAuditRecord {
  timestamp: number;
  filename: string;
  action: string;
  diff?: any;
  sessionId?: string;
<<<<<<< HEAD
  hash?: string;
=======
>>>>>>> 9f492dd7a98e4a8bb5157fa332edc8af17e007ea
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
<<<<<<< HEAD
    // Integrity hash (SHA-256 of JSON payload)
    try {
      const hash = crypto.createHash('sha256').update(JSON.stringify(rec)).digest('hex');
      rec.hash = hash;
    } catch { /* ignore */ }
=======
>>>>>>> 9f492dd7a98e4a8bb5157fa332edc8af17e007ea
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
<<<<<<< HEAD
  const { searchParams } = new URL(request.url);
  let data = auditStore.slice().reverse();
  // Filtering
  const action = searchParams.get('action');
  const filename = searchParams.get('filename');
  const sessionId = searchParams.get('sessionId');
  if (action) data = data.filter(r => r.action === action);
  if (filename) data = data.filter(r => r.filename === filename);
  if (sessionId) data = data.filter(r => r.sessionId === sessionId);
  // Pagination
  const offset = parseInt(searchParams.get('offset') || '0', 10);
  const limit = Math.min(parseInt(searchParams.get('limit') || '50', 10), 200);
  data = data.slice(offset, offset + limit);
  return withCors(NextResponse.json({ success: true, data }), request);
=======
  return withCors(NextResponse.json({ success: true, data: auditStore.slice().reverse() }), request);
>>>>>>> 9f492dd7a98e4a8bb5157fa332edc8af17e007ea
}

export async function OPTIONS(request: NextRequest) { return preflight(request); }
