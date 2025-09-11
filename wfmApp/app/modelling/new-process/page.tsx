"use client"

import React, { useState } from 'react';
import dynamic from 'next/dynamic';
import { AppShell } from '@/components/app-shell';
import { processApiService, ProcessCreate } from '@/services/processApi';
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

export default function NewProcessPage() {
  const { toast } = useToast();
  const [showBpmnEditor, setShowBpmnEditor] = useState(false);
  const [processName, setProcessName] = useState('New Process');
  const [isDirty, setIsDirty] = useState(false);

  const handleCreateNewProcess = () => {
    setProcessName('New Process');
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
      const processData: ProcessCreate = {
        name: processName,
        description: `Process created from BPMN editor`,
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
          description: 'Process saved successfully!',
        });
      } else {
        throw new Error(response.error || 'Failed to save process');
      }

      setIsDirty(false);
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
      <AppShell title="New Process" subtitle="Create a new business process">
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
              ← Back to New Process
            </button>
          </div>
          <BpmnModelerComponent
            onSave={handleSaveProcess}
            onClose={() => setShowBpmnEditor(false)}
            autoCreateDiagram={true}
            initialXml=""
            onDirtyChange={setIsDirty}
            isDirty={isDirty}
          />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell title="New Process" subtitle="Create a new business process">
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-center">
          <div className="text-gray-500 mb-4">
            <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Create New FSM Process
          </h3>
          <p className="text-gray-500 mb-6">
            Design field service workflows and business processes using our visual process designer
          </p>
          <div className="space-x-4">
            <button 
              onClick={handleCreateNewProcess}
              className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded"
            >
              Create from Scratch
            </button>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
