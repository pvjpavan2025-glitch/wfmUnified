"use client";

import React, { useEffect, useRef } from 'react';
import 'bpmn-js/dist/assets/diagram-js.css';
import 'bpmn-js/dist/assets/bpmn-font/css/bpmn.css';

interface WorkflowStep {
  step_id: string;
  name: string;
  step_type: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  started_at?: string;
  completed_at?: string;
}

interface BpmnViewerProps {
  xml: string;
  executionData?: WorkflowStep[];
  className?: string;
}

const statusColors = {
  pending: '#fbbf24', // yellow
  running: '#3b82f6', // blue
  completed: '#10b981', // green
  failed: '#ef4444', // red
  skipped: '#6b7280' // gray
};

const BpmnViewer: React.FC<BpmnViewerProps> = ({ xml, executionData = [], className = '' }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<any | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Dynamically import BPMN.js to avoid ES module issues
    import('bpmn-js/lib/Viewer').then((BpmnJS) => {
      if (!containerRef.current) return;
      
      const viewer = new BpmnJS.default({
        container: containerRef.current,
        width: '100%',
        height: '400px'
      });

      viewerRef.current = viewer;

      // Load BPMN diagram
      loadDiagram(viewer, xml);
    }).catch((error) => {
      console.error('Failed to load BPMN viewer:', error);
    });


    return () => {
      if (viewerRef.current) {
        viewerRef.current.destroy();
      }
    };
  }, [xml]);

  useEffect(() => {
    if (viewerRef.current && executionData.length > 0) {
      colorizeElements(viewerRef.current, executionData);
    }
  }, [executionData]);

  const loadDiagram = async (viewer: any, diagramXml: string) => {
    try {
      await viewer.importXML(diagramXml);
      
      // Fit diagram to viewport
      const canvas = viewer.get('canvas') as any;
      canvas.zoom('fit-viewport');
      
      // Apply execution status colors if available
      if (executionData.length > 0) {
        colorizeElements(viewer, executionData);
      }
    } catch (error) {
      console.error('Error loading BPMN diagram:', error);
    }
  };

  const colorizeElements = (viewer: any, steps: WorkflowStep[]) => {
    try {
      const canvas = viewer.get('canvas') as any;
      const elementRegistry = viewer.get('elementRegistry') as any;
      
      // Reset all elements to default color first
      const allElements = elementRegistry.getAll();
      allElements.forEach((element: any) => {
        if (element.businessObject && element.businessObject.$type !== 'bpmn:Process') {
          canvas.removeMarker(element.id, 'highlight-pending');
          canvas.removeMarker(element.id, 'highlight-running');
          canvas.removeMarker(element.id, 'highlight-completed');
          canvas.removeMarker(element.id, 'highlight-failed');
          canvas.removeMarker(element.id, 'highlight-skipped');
        }
      });

      // Apply colors based on execution status
      steps.forEach((step) => {
        const element = elementRegistry.get(step.step_id);
        if (element) {
          // Add CSS class based on status
          canvas.addMarker(element.id, `highlight-${step.status}`);
          
          // Also set stroke color directly
          const gfx = elementRegistry.getGraphics(element);
          if (gfx) {
            const shape = gfx.querySelector('.djs-visual > *');
            if (shape) {
              shape.style.stroke = statusColors[step.status];
              shape.style.strokeWidth = '3px';
              
              // For filled elements, also set fill with transparency
              if (step.status === 'completed') {
                shape.style.fill = statusColors[step.status] + '20'; // 20% opacity
              } else if (step.status === 'failed') {
                shape.style.fill = statusColors[step.status] + '20';
              } else if (step.status === 'running') {
                shape.style.fill = statusColors[step.status] + '20';
                // Add pulsing animation for running tasks
                shape.style.animation = 'pulse 2s infinite';
              }
            }
          }
        }
      });
    } catch (error) {
      console.error('Error colorizing BPMN elements:', error);
    }
  };

  return (
    <div className={`bpmn-viewer-container ${className}`}>
      <div 
        ref={containerRef} 
        className="w-full h-full"
        style={{ minHeight: '400px' }}
      />
      
      {/* Legend */}
      <div className="absolute top-4 right-4 bg-white p-3 rounded-lg shadow-lg border">
        <h4 className="text-sm font-semibold mb-2">Execution Status</h4>
        <div className="space-y-1 text-xs">
          <div className="flex items-center gap-2">
            <div 
              className="w-3 h-3 border-2 rounded" 
              style={{ borderColor: statusColors.pending }}
            />
            <span>Pending</span>
          </div>
          <div className="flex items-center gap-2">
            <div 
              className="w-3 h-3 border-2 rounded" 
              style={{ borderColor: statusColors.running }}
            />
            <span>Running</span>
          </div>
          <div className="flex items-center gap-2">
            <div 
              className="w-3 h-3 border-2 rounded" 
              style={{ borderColor: statusColors.completed }}
            />
            <span>Completed</span>
          </div>
          <div className="flex items-center gap-2">
            <div 
              className="w-3 h-3 border-2 rounded" 
              style={{ borderColor: statusColors.failed }}
            />
            <span>Failed</span>
          </div>
          <div className="flex items-center gap-2">
            <div 
              className="w-3 h-3 border-2 rounded" 
              style={{ borderColor: statusColors.skipped }}
            />
            <span>Skipped</span>
          </div>
        </div>
      </div>

      <style jsx>{`
        .bpmn-viewer-container {
          position: relative;
        }
        
        @keyframes pulse {
          0% {
            opacity: 1;
          }
          50% {
            opacity: 0.5;
          }
          100% {
            opacity: 1;
          }
        }
        
        :global(.highlight-pending .djs-visual > *) {
          stroke: ${statusColors.pending} !important;
          stroke-width: 3px !important;
        }
        
        :global(.highlight-running .djs-visual > *) {
          stroke: ${statusColors.running} !important;
          stroke-width: 3px !important;
          animation: pulse 2s infinite;
        }
        
        :global(.highlight-completed .djs-visual > *) {
          stroke: ${statusColors.completed} !important;
          stroke-width: 3px !important;
          fill: ${statusColors.completed}20 !important;
        }
        
        :global(.highlight-failed .djs-visual > *) {
          stroke: ${statusColors.failed} !important;
          stroke-width: 3px !important;
          fill: ${statusColors.failed}20 !important;
        }
        
        :global(.highlight-skipped .djs-visual > *) {
          stroke: ${statusColors.skipped} !important;
          stroke-width: 3px !important;
        }
      `}</style>
    </div>
  );
};

export default BpmnViewer;
