'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Save, Download, Upload, Play, Square, RotateCcw } from 'lucide-react';

// Dynamic imports for BPMN.js to avoid SSR issues
let BpmnModeler: any = null;
let BpmnPropertiesPanelModule: any = null;
let BpmnPropertiesProviderModule: any = null;
let CamundaPlatformPropertiesProviderModule: any = null;
let ColorPickerModule: any = null;
let MinimapModule: any = null;
let camundaModdleDescriptor: any = null;

interface BpmnModelerProps {
  onSave?: (xml: string, svg?: string) => void;
  onClose?: () => void;
  initialXml?: string;
  readOnly?: boolean;
}

const BpmnModelerComponent: React.FC<BpmnModelerProps> = ({ 
  onSave, 
  onClose, 
  initialXml,
  readOnly = false 
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const propertiesPanelRef = useRef<HTMLDivElement>(null);
  const [modeler, setModeler] = useState<any>(null);
  const [xml, setXml] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [isExecuting, setIsExecuting] = useState(false);

  // Default BPMN diagram
  const defaultXml = `<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" 
                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" 
                  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" 
                  xmlns:di="http://www.omg.org/spec/DD/20100524/DI" 
                  id="Definitions_1" 
                  targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="Process_1" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1"/>
  </bpmn:process>
  <bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Process_1">
      <bpmndi:BPMNShape id="_BPMNShape_StartEvent_2" bpmnElement="StartEvent_1">
        <dc:Bounds x="179" y="79" width="36" height="36"/>
      </bpmndi:BPMNShape>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>`;

  useEffect(() => {
    const loadBpmnModules = async () => {
      try {
        // Dynamic imports to avoid SSR issues
        const [
          BpmnModelerModule,
          PropertiesPanelModule,
          ColorPickerModuleImport,
          MinimapModuleImport,
          CamundaModdle
        ] = await Promise.all([
          import('bpmn-js/lib/Modeler'),
          import('bpmn-js-properties-panel'),
          import('bpmn-js-color-picker').catch(() => null), // Handle missing module gracefully
          import('diagram-js-minimap'),
          import('camunda-bpmn-moddle/resources/camunda.json')
        ]);

        BpmnModeler = BpmnModelerModule.default;
        BpmnPropertiesPanelModule = PropertiesPanelModule.BpmnPropertiesPanelModule;
        BpmnPropertiesProviderModule = PropertiesPanelModule.BpmnPropertiesProviderModule;
        CamundaPlatformPropertiesProviderModule = PropertiesPanelModule.CamundaPlatformPropertiesProviderModule;
        ColorPickerModule = ColorPickerModuleImport?.default || null;
        MinimapModule = MinimapModuleImport.default;
        camundaModdleDescriptor = CamundaModdle.default;

        // Load CSS dynamically
        const cssFiles = [
          'https://unpkg.com/bpmn-js@18.6.3/dist/assets/diagram-js.css',
          'https://unpkg.com/bpmn-js@18.6.3/dist/assets/bpmn-font/css/bpmn.css',
          'https://unpkg.com/@bpmn-io/properties-panel@3.0.0/dist/assets/properties-panel.css',
          'https://unpkg.com/diagram-js-minimap@4.0.0/assets/diagram-js-minimap.css'
        ];

        cssFiles.forEach(href => {
          if (!document.querySelector(`link[href="${href}"]`)) {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = href;
            document.head.appendChild(link);
          }
        });

        initializeModeler();
      } catch (err) {
        console.error('Failed to load BPMN modules:', err);
        setError('Failed to load BPMN modeler components');
        setIsLoading(false);
      }
    };

    loadBpmnModules();
  }, []);

  const initializeModeler = async () => {
    if (!containerRef.current || !propertiesPanelRef.current || !BpmnModeler) return;

    try {
      setIsLoading(true);
      setError('');

      const newModeler = new BpmnModeler({
        container: containerRef.current,
        propertiesPanel: {
          parent: propertiesPanelRef.current
        },
        additionalModules: [
          BpmnPropertiesPanelModule,
          BpmnPropertiesProviderModule,
          CamundaPlatformPropertiesProviderModule,
          ...(ColorPickerModule ? [ColorPickerModule] : []),
          MinimapModule
        ].filter(Boolean),
        moddleExtensions: {
          camunda: camundaModdleDescriptor
        },
        keyboard: {
          bindTo: document
        }
      });

      setModeler(newModeler);

      // Import initial diagram
      const xmlToImport = initialXml || defaultXml;
      await newModeler.importXML(xmlToImport);
      setXml(xmlToImport);

      // Fit viewport to diagram
      const canvas = newModeler.get('canvas');
      canvas.zoom('fit-viewport');

      setIsLoading(false);
    } catch (err) {
      console.error('Failed to initialize BPMN modeler:', err);
      setError('Failed to initialize BPMN modeler');
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!modeler) return;

    try {
      const { xml: savedXml } = await modeler.saveXML({ format: true });
      const { svg } = await modeler.saveSVG();
      setXml(savedXml);
      
      if (onSave) {
        onSave(savedXml, svg);
      }
    } catch (err) {
      console.error('Failed to save diagram:', err);
      setError('Failed to save diagram');
    }
  };

  const handleDownload = async () => {
    if (!modeler) return;

    try {
      const { xml: savedXml } = await modeler.saveXML({ format: true });
      const blob = new Blob([savedXml], { type: 'application/xml' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'workflow.bpmn';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download diagram:', err);
      setError('Failed to download diagram');
    }
  };

  const handleUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !modeler) return;

    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const xmlContent = e.target?.result as string;
        await modeler.importXML(xmlContent);
        setXml(xmlContent);
        const canvas = modeler.get('canvas');
        canvas.zoom('fit-viewport');
      } catch (err) {
        console.error('Failed to import diagram:', err);
        setError('Failed to import diagram');
      }
    };
    reader.readAsText(file);
  };

  const handleExecute = async () => {
    if (!modeler) return;

    try {
      setIsExecuting(true);
      const { xml: currentXml } = await modeler.saveXML({ format: true });
      
      // Call the process engine API
      const processEngineUrl = process.env.NEXT_PUBLIC_PROCESS_ENGINE_URL || 'http://localhost:8090';
      const response = await fetch(`${processEngineUrl}/workflows/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          bpmn_xml: currentXml,
          variables: {}
        })
      });

      if (response.ok) {
        const result = await response.json();
        alert(`Workflow executed successfully! Instance ID: ${result.instance_id}`);
      } else {
        throw new Error('Failed to execute workflow');
      }
    } catch (err) {
      console.error('Failed to execute workflow:', err);
      setError('Failed to execute workflow');
    } finally {
      setIsExecuting(false);
    }
  };

  const handleReset = async () => {
    if (!modeler) return;

    try {
      await modeler.importXML(defaultXml);
      setXml(defaultXml);
      const canvas = modeler.get('canvas');
      canvas.zoom('fit-viewport');
    } catch (err) {
      console.error('Failed to reset diagram:', err);
      setError('Failed to reset diagram');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>Loading BPMN Modeler...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="m-4">
        <CardHeader>
          <CardTitle className="text-red-600">Error</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-red-600 mb-4">{error}</p>
          <Button onClick={() => window.location.reload()}>Reload</Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Toolbar */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-semibold text-gray-900">BPMN Workflow Modeler</h1>
            {onClose && (
              <Button variant="ghost" onClick={onClose} className="ml-4">
                ← Back
              </Button>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            {!readOnly && (
              <>
                <Button onClick={handleSave} className="flex items-center space-x-1">
                  <Save className="w-4 h-4" />
                  <span>Save</span>
                </Button>
                
                <Button onClick={handleExecute} disabled={isExecuting} variant="secondary" className="flex items-center space-x-1">
                  <Play className="w-4 h-4" />
                  <span>{isExecuting ? 'Executing...' : 'Execute'}</span>
                </Button>
                
                <Button onClick={handleReset} variant="outline" className="flex items-center space-x-1">
                  <RotateCcw className="w-4 h-4" />
                  <span>Reset</span>
                </Button>
              </>
            )}
            
            <Button onClick={handleDownload} variant="outline" className="flex items-center space-x-1">
              <Download className="w-4 h-4" />
              <span>Download</span>
            </Button>
            
            {!readOnly && (
              <label className="cursor-pointer">
                <Button variant="outline" className="flex items-center space-x-1">
                  <Upload className="w-4 h-4" />
                  <span>Upload</span>
                </Button>
                <input
                  type="file"
                  accept=".bpmn,.xml"
                  onChange={handleUpload}
                  className="hidden"
                />
              </label>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* BPMN Canvas */}
        <div className="flex-1 relative">
          <div 
            ref={containerRef} 
            className="absolute inset-0 bg-white"
            style={{ height: '100%', width: '100%' }}
          />
        </div>

        {/* Properties Panel */}
        <div className="w-80 bg-white border-l border-gray-200 overflow-auto">
          <div className="p-4 border-b border-gray-200">
            <h3 className="font-medium text-gray-900">Properties</h3>
          </div>
          <div 
            ref={propertiesPanelRef} 
            className="p-4"
            style={{ minHeight: '400px' }}
          />
        </div>
      </div>
    </div>
  );
};

export default BpmnModelerComponent;
