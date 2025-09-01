import { NextRequest, NextResponse } from 'next/server';

// Simple in-memory storage as Redis alternative for now
// In production, replace this with actual Redis implementation
const bpmnStorage = new Map<string, {
  id: string;
  xml: string;
  name: string;
  timestamp: string;
}>();

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { xml, name, timestamp } = body;

    if (!xml || typeof xml !== 'string') {
      return NextResponse.json(
        { error: 'Invalid XML content' },
        { status: 400 }
      );
    }

    // Generate unique ID
    const id = `bpmn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // Store the BPMN data
    const bpmnData = {
      id,
      xml,
      name: name || `workflow_${Date.now()}`,
      timestamp: timestamp || new Date().toISOString()
    };

    bpmnStorage.set(id, bpmnData);

    console.log(`BPMN saved with ID: ${id}, size: ${xml.length} chars`);

    return NextResponse.json({
      success: true,
      id,
      message: 'BPMN workflow saved successfully'
    });

  } catch (error) {
    console.error('Error saving BPMN:', error);
    return NextResponse.json(
      { 
        error: 'Failed to save BPMN workflow',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');

    if (id) {
      // Get specific BPMN by ID
      const bpmnData = bpmnStorage.get(id);
      if (!bpmnData) {
        return NextResponse.json(
          { error: 'BPMN workflow not found' },
          { status: 404 }
        );
      }
      return NextResponse.json(bpmnData);
    } else {
      // List all saved BPMNs
      const allBpmns = Array.from(bpmnStorage.values()).map(({ xml, ...rest }) => ({
        ...rest,
        xmlSize: xml.length
      }));
      
      return NextResponse.json({
        workflows: allBpmns,
        count: allBpmns.length
      });
    }

  } catch (error) {
    console.error('Error retrieving BPMN:', error);
    return NextResponse.json(
      { 
        error: 'Failed to retrieve BPMN workflow',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');

    if (!id) {
      return NextResponse.json(
        { error: 'Missing workflow ID' },
        { status: 400 }
      );
    }

    const deleted = bpmnStorage.delete(id);
    
    if (!deleted) {
      return NextResponse.json(
        { error: 'BPMN workflow not found' },
        { status: 404 }
      );
    }

    return NextResponse.json({
      success: true,
      message: 'BPMN workflow deleted successfully'
    });

  } catch (error) {
    console.error('Error deleting BPMN:', error);
    return NextResponse.json(
      { 
        error: 'Failed to delete BPMN workflow',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}
