import { NextRequest, NextResponse } from 'next/server';
import { withCors, preflight } from '@/lib/cors';
import { promises as fs } from 'fs';
import path from 'path';

const AUDIT_DIR = process.env.AUDIT_LOG_DIR || path.join(process.cwd(), 'tmp');
const AUDIT_FILE = path.join(AUDIT_DIR, 'conflict-audit.json');

export async function GET(request: NextRequest) {
  try {
    const data = await fs.readFile(AUDIT_FILE, 'utf-8');
    return withCors(new NextResponse(data, {
      headers: {
        'Content-Type': 'application/json',
        'Content-Disposition': 'attachment; filename="conflict-audit.json"'
      }
    }), request);
  } catch (e) {
    return NextResponse.json({ success: false, error: 'No audit log available' }, { status: 404 });
  }
}

export async function OPTIONS(request: NextRequest) { return preflight(request); }
