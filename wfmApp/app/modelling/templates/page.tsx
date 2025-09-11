"use client"

import React, { useState, useEffect, useRef } from 'react';
import dynamic from 'next/dynamic';
import { AppShell } from '@/components/app-shell';
import { 
  PlusIcon
} from '@heroicons/react/24/outline';
import { processApiService, Template } from '@/services/processApi';
import { useToast } from '@/hooks/use-toast';
import { ProcessNameEditor } from '../../../components/modelling/ProcessNameEditor';

// Dynamic imports for components
const BpmnModelerComponent = dynamic(
  () => import('@/components/modelling/BpmnModeler'),
  { 
    ssr: false,
    loading: () => <div className="flex items-center justify-center h-96">Loading BPMN Editor...</div>
  }
);

export default function TemplatesPage() {
  const { toast } = useToast();
  const [showBpmnEditor, setShowBpmnEditor] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [processName, setProcessName] = useState('New Process');
  const [isDirty, setIsDirty] = useState(false);
  const [initialXml, setInitialXml] = useState<string>('');
  
  // State for real data
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Prevent duplicate fetches under React StrictMode by tracking last loaded
  const lastLoadedRef = useRef<boolean>(false);

  // Load data when component mounts
  useEffect(() => {
    if (lastLoadedRef.current) return;
    lastLoadedRef.current = true;
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const templatesResponse = await processApiService.listTemplates();
      if (templatesResponse.data) {
        setTemplates(templatesResponse.data);
      } else if (templatesResponse.error) {
        setError(templatesResponse.error);
      }
    } catch (err) {
      // If there's an error, just set empty templates instead of throwing
      setTemplates([]);
      console.log('No templates found or error occurred:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNewProcess = () => {
    setProcessName('New Process');
    setSelectedTemplate(null);
    setInitialXml('');
    setShowBpmnEditor(true);
  };

  const handleCreateFromTemplate = (template: Template) => {
    setProcessName(template.name);
    setSelectedTemplate(template);
    setInitialXml(template.bpmn_xml);
    setShowBpmnEditor(true);
  };

  const handleSaveProcess = async (xml: string) => {
    if (!processName.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Process name cannot be empty.',
        variant: 'destructive',
      });
      return;
    }

    try {
      const processData = {
        name: processName,
        description: `Process created from template`,
        bpmn_xml: xml,
        version: "1.0.0",
        category: "General",
        tags: ["bpmn", "workflow"],
        metadata: {},
        created_by: "current_user",
        tenant_id: "default"
      };

      const response = await processApiService.createProcess(processData, "current_user");
      
      if (response.data) {
        toast({
          title: 'Success',
          description: 'Process created from template successfully!',
        });
      } else {
        throw new Error(response.error || 'Failed to save process');
      }

      setIsDirty(false);
      loadData(); // Refresh the list in background
    } catch (err) {
      toast({
        title: 'Error Saving Process',
        description: err instanceof Error ? err.message : 'An unknown error occurred.',
        variant: 'destructive',
      });
    }
  };

  if (showBpmnEditor) {
    return (
      <AppShell title="Create from Template" subtitle="Create process from template">
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <ProcessNameEditor
              name={processName}
              onSave={(newName) => {
                setProcessName(newName);
                setIsDirty(true);
              }}
              isDirty={isDirty}
            />
            <button
              onClick={() => setShowBpmnEditor(false)}
              className="text-gray-500 hover:text-gray-700 text-sm"
            >
              ← Back to Templates
            </button>
          </div>
          <BpmnModelerComponent
            onSave={handleSaveProcess}
            onClose={() => setShowBpmnEditor(false)}
            autoCreateDiagram={!selectedTemplate}
            initialXml={initialXml}
            onDirtyChange={setIsDirty}
            isDirty={isDirty}
          />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell title="Templates" subtitle="Create processes from templates">
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-medium text-gray-900">Templates</h3>
          <button
            onClick={handleCreateNewProcess}
            className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded"
          >
            Create New Template
          </button>
        </div>
        
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-500">Loading templates...</p>
          </div>
        ) : error ? (
          <div className="text-center py-8 space-y-2">
            <p className="text-red-500">{error}</p>
            {(process.env.NEXT_PUBLIC_BPMN_OFFLINE_MODE === 'true' || /offline|connrefused|failed to fetch/i.test(error)) && (
              <p className="text-xs text-gray-500">Backend unreachable (offline mode). Showing empty list.</p>
            )}
          </div>
        ) : templates.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500">No templates found. Create templates from existing processes.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {templates.map((template, idx) => (
              <div key={template.id || `${template.name}-${idx}` } className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="text-sm font-medium text-gray-900 mb-1">{template.name}</h4>
                    <p className="text-xs text-gray-500 mb-2">{template.description}</p>
                    <div className="flex items-center space-x-2 text-xs text-gray-500">
                      <span>Usage: {template.usage_count}</span>
                      <span>•</span>
                      <span>Template</span>
                    </div>
                  </div>
                  <button
                    onClick={() => handleCreateFromTemplate(template)}
                    className="text-blue-600 hover:text-blue-900 p-1"
                    title="Use Template"
                  >
                    <PlusIcon className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
