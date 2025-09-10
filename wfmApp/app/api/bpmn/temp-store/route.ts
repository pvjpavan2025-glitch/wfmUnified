import { NextRequest, NextResponse } from 'next/server';
import { withCors, preflight } from '@/lib/cors';

// Mock Redis interface - replace with actual Redis client
interface TempStorage {
  [key: string]: {
    xml: string;
    filename: string;
    timestamp: number;
    sessionId: string;
  };
}

// In-memory storage (replace with Redis in production)
const tempStorage: TempStorage = {};

// Cleanup function to remove old entries
const cleanup = () => {
  const now = Date.now();
  const maxAge = 24 * 60 * 60 * 1000; // 24 hours
  
  Object.keys(tempStorage).forEach(key => {
    if (now - tempStorage[key].timestamp > maxAge) {
      delete tempStorage[key];
    }
  });
};

export async function POST(request: NextRequest) {
  try {
    const { xml, filename, sessionId, overwrite = false } = await request.json();
    
    if (!xml || !filename || !sessionId) {
      return NextResponse.json(
        { error: 'Missing required fields: xml, filename, sessionId' },
        { status: 400 }
      );
    }
    
    // Cleanup old entries
    cleanup();
    
    // Generate storage key
    const key = `bpmn_${sessionId}_${filename}_${Date.now()}`;
    
    // Check if similar key exists and handle overwrite
    const existingKeys = Object.keys(tempStorage).filter(k => 
      k.includes(sessionId) && k.includes(filename.replace(/\.\w+$/, ''))
    );
    
    if (existingKeys.length > 0 && overwrite) {
      // Remove existing entries for this session and filename
      existingKeys.forEach(existingKey => {
        delete tempStorage[existingKey];
      });
    }
    
    // Store the data
    tempStorage[key] = {
      xml,
      filename,
      timestamp: Date.now(),
      sessionId
    };
    
  return withCors(NextResponse.json({
      success: true,
      key,
      message: overwrite ? 'BPMN stored (overwrote existing)' : 'BPMN stored successfully'
  }), request);
    
  } catch (error) {
    console.error('Error storing BPMN temporarily:', error);
    return NextResponse.json(
      { error: 'Failed to store BPMN temporarily' },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const key = searchParams.get('key');
    const sessionId = searchParams.get('sessionId');
    
    if (!key && !sessionId) {
      return NextResponse.json(
        { error: 'Missing key or sessionId parameter' },
        { status: 400 }
      );
    }
    
    // Cleanup old entries
    cleanup();
    
    if (key) {
      // Get specific item by key
      const item = tempStorage[key];
      if (!item) {
        return NextResponse.json(
          { error: 'BPMN not found or expired' },
          { status: 404 }
        );
      }
      
  return withCors(NextResponse.json({
        success: true,
        data: item
  }), request);
    }
    
    if (sessionId) {
      // Get all items for session
      const sessionItems = Object.entries(tempStorage)
        .filter(([k, v]) => v.sessionId === sessionId)
        .map(([k, v]) => ({ key: k, ...v }));
      
  return withCors(NextResponse.json({
        success: true,
        data: sessionItems
  }), request);
    }
    
  } catch (error) {
    console.error('Error retrieving BPMN:', error);
    return NextResponse.json(
      { error: 'Failed to retrieve BPMN' },
      { status: 500 }
    );
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const key = searchParams.get('key');
    const sessionId = searchParams.get('sessionId');
    
    if (key) {
      // Delete specific item
      if (tempStorage[key]) {
        delete tempStorage[key];
  return withCors(NextResponse.json({ success: true, message: 'BPMN deleted' }), request);
      } else {
        return NextResponse.json(
          { error: 'BPMN not found' },
          { status: 404 }
        );
      }
    }
    
    if (sessionId) {
      // Delete all items for session
      const deleted = Object.keys(tempStorage)
        .filter(k => tempStorage[k].sessionId === sessionId);
      
      deleted.forEach(k => delete tempStorage[k]);
      
        return withCors(NextResponse.json({
          success: true,
          message: `Deleted ${deleted.length} items for session`
        }), request);
    }
    
    return NextResponse.json(
      { error: 'Missing key or sessionId parameter' },
      { status: 400 }
    );
    
  } catch (error) {
    console.error('Error deleting BPMN:', error);
    return NextResponse.json(
      { error: 'Failed to delete BPMN' },
      { status: 500 }
    );
  }
}

export async function OPTIONS(request: NextRequest) {
  return preflight(request);
}
