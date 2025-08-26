import React, { useEffect, useRef, useState } from 'react';
import BpmnModeler from 'bpmn-js/lib/Modeler';
import 'bpmn-js/dist/assets/diagram-js.css';
import 'bpmn-js/dist/assets/bpmn-font/css/bpmn.css';
import 'bpmn-js-properties-panel/dist/assets/properties-panel.css';
import 'bpmn-js-properties-panel/dist/assets/element-templates.css';

import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { useToast } from './ui/use-toast';
import { Download, Upload, Play, Save, Trash2 } from 'lucide-react';

interface BpmnModelerProps {}

export const BpmnModeler: React.FC<BpmnModelerProps> = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const propertiesPanelRef = useRef<HTMLDivElement>(null);
  const [modeler, setModeler] = useState<BpmnModeler | null>(null);
  const [workflowName, setWorkflowName] = useState('');
  const [workflowVersion, setWorkflowVersion] = useState('1.0.0');
  const { toast } = useToast();

  useEffect(() => {
    if (containerRef.current && propertiesPanelRef.current) {
      // Initialize BPMN modeler
      const bpmnModeler = new BpmnModeler({
        container: containerRef.current,
        propertiesPanel: {
          parent: propertiesPanelRef.current
        },
        additionalModules: [
          // Add properties panel
          require('bpmn-js-properties-panel').default,
          // Add Camunda BPMN moddle for extended BPMN support
          require('camunda-bpmn-moddle').default
        ],
        moddleExtensions: {
          camunda: require('camunda-bpmn-moddle/resources/camunda')
        }
      });

      // Load default BPMN diagram
      const defaultBpmn = `<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" 
                   xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" 
                   xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" 
                   xmlns:di="http://www.omg.org/spec/DD/20100524/DI" 
                   id="Definitions_1" 
                   targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="Process_1" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1" name="Start">
      <bpmn:outgoing>Flow_1</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:task id="Task_1" name="Sample Task">
      <bpmn:incoming>Flow_1</bpmn:incoming>
      <bpmn:outgoing>Flow_2</bpmn:outgoing>
    </bpmn:task>
    <bpmn:endEvent id="EndEvent_1" name="End">
      <bpmn:incoming>Flow_2</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_1" sourceRef="StartEvent_1" targetRef="Task_1" />
    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_1" targetRef="EndEvent_1" />
  </bpmn:process>
  <bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Process_1">
      <bpmndi:BPMNShape id="StartEvent_1_di" bpmnElement="StartEvent_1">
        <dc:Bounds x="152" y="102" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Task_1_di" bpmnElement="Task_1">
        <dc:Bounds x="240" y="80" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="EndEvent_1_di" bpmnElement="EndEvent_1">
        <dc:Bounds x="392" y="102" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="Flow_1_di" bpmnElement="Flow_1">
        <di:waypoint x="188" y="120" />
        <di:waypoint x="240" y="120" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_2_di" bpmnElement="Flow_2">
        <di:waypoint x="340" y="120" />
        <di:waypoint x="392" y="120" />
      </bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>`;

      bpmnModeler.importXML(defaultBpmn).then(() => {
        bpmnModeler.get('canvas').zoom('fit-viewport');
        toast({
          title: "BPMN Modeler Ready",
          description: "Default workflow template loaded successfully.",
        });
      }).catch((err: Error) => {
        console.error('Error importing BPMN:', err);
        toast({
          title: "Error",
          description: "Failed to load default workflow template.",
          variant: "destructive",
        });
      });

      setModeler(bpmnModeler);

      return () => {
        bpmnModeler.destroy();
      };
    }
  }, [toast]);

  const handleSave = async () => {
    if (!modeler) return;

    try {
      const { xml } = await modeler.saveXML({ format: true });
      
      // Create blob and download
      const blob = new Blob([xml], { type: 'application/xml' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${workflowName || 'workflow'}.bpmn`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast({
        title: "Success",
        description: "BPMN workflow saved successfully.",
      });
    } catch (error) {
      console.error('Error saving BPMN:', error);
      toast({
        title: "Error",
        description: "Failed to save BPMN workflow.",
        variant: "destructive",
      });
    }
  };

  const handleUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !modeler) return;

    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const xml = e.target?.result as string;
        await modeler.importXML(xml);
        modeler.get('canvas').zoom('fit-viewport');
        
        toast({
          title: "Success",
          description: "BPMN workflow uploaded successfully.",
        });
      } catch (error) {
        console.error('Error importing BPMN:', error);
        toast({
          title: "Error",
          description: "Failed to import BPMN workflow.",
          variant: "destructive",
        });
      }
    };
    reader.readAsText(file);
  };

  const handleDeploy = async () => {
    if (!modeler) return;

    try {
      const { xml } = await modeler.saveXML({ format: true });
      
      // Send to backend API
      const formData = new FormData();
      formData.append('file', new Blob([xml], { type: 'application/xml' }), `${workflowName || 'workflow'}.bpmn`);
      formData.append('name', workflowName || 'Unnamed Workflow');
      formData.append('version', workflowVersion);

      const response = await fetch('/upload-bpmn', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        toast({
          title: "Success",
          description: `Workflow deployed successfully. ID: ${result.workflow_definition.id}`,
        });
      } else {
        throw new Error('Deployment failed');
      }
    } catch (error) {
      console.error('Error deploying workflow:', error);
      toast({
        title: "Error",
        description: "Failed to deploy workflow.",
        variant: "destructive",
      });
    }
  };

  const handleClear = () => {
    if (!modeler) return;
    
    // Clear the canvas
    modeler.clear();
    toast({
      title: "Canvas Cleared",
      description: "Workflow canvas has been cleared.",
    });
  };

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-lg font-semibold">BPMN Workflow Modeler</h1>
          </div>
          
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-2">
              <Label htmlFor="workflow-name">Name:</Label>
              <Input
                id="workflow-name"
                placeholder="Workflow Name"
                value={workflowName}
                onChange={(e) => setWorkflowName(e.target.value)}
                className="w-40"
              />
            </div>
            <div className="flex items-center space-x-2">
              <Label htmlFor="workflow-version">Version:</Label>
              <Input
                id="workflow-version"
                placeholder="1.0.0"
                value={workflowVersion}
                onChange={(e) => setWorkflowVersion(e.target.value)}
                className="w-20"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Toolbar */}
      <div className="border-b bg-muted/40">
        <div className="container flex h-12 items-center space-x-2">
          <Button variant="outline" size="sm" onClick={handleSave}>
            <Save className="h-4 w-4 mr-2" />
            Save
          </Button>
          <Button variant="outline" size="sm" onClick={handleUpload}>
            <Upload className="h-4 w-4 mr-2" />
            Upload
            <Input
              type="file"
              accept=".bpmn,.xml"
              onChange={handleUpload}
              className="hidden"
              id="upload-input"
            />
          </Button>
          <Button variant="outline" size="sm" onClick={handleDeploy}>
            <Play className="h-4 w-4 mr-2" />
            Deploy
          </Button>
          <Button variant="outline" size="sm" onClick={handleClear}>
            <Trash2 className="h-4 w-4 mr-2" />
            Clear
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex">
        {/* BPMN Canvas */}
        <div className="flex-1 relative">
          <div
            ref={containerRef}
            className="w-full h-full border-r"
            style={{ background: '#f8f9fa' }}
          />
        </div>

        {/* Properties Panel */}
        <div className="w-80 border-l bg-background">
          <Tabs defaultValue="properties" className="h-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="properties">Properties</TabsTrigger>
              <TabsTrigger value="palette">Palette</TabsTrigger>
            </TabsList>
            
            <TabsContent value="properties" className="h-full">
              <div
                ref={propertiesPanelRef}
                className="h-full overflow-auto p-4"
              />
            </TabsContent>
            
            <TabsContent value="palette" className="h-full p-4">
              <Card>
                <CardHeader>
                  <CardTitle>BPMN Elements</CardTitle>
                  <CardDescription>
                    Drag and drop elements to create your workflow
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="grid grid-cols-2 gap-2">
                    <div className="p-2 border rounded cursor-move hover:bg-muted">
                      <div className="text-xs font-medium">Start Event</div>
                    </div>
                    <div className="p-2 border rounded cursor-move hover:bg-muted">
                      <div className="text-xs font-medium">Task</div>
                    </div>
                    <div className="p-2 border rounded cursor-move hover:bg-muted">
                      <div className="text-xs font-medium">Gateway</div>
                    </div>
                    <div className="p-2 border rounded cursor-move hover:bg-muted">
                      <div className="text-xs font-medium">End Event</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
};
