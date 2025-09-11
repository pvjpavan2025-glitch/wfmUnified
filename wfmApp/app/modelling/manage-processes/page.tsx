"use client"

import React, { useState, useEffect, useRef } from 'react';
import dynamic from 'next/dynamic';
import { AppShell } from '@/components/app-shell';
import { 
  PlusIcon, 
  TrashIcon,
  DocumentIcon
} from '@heroicons/react/24/outline';
import { processApiService, Process, ProcessUpdate } from '@/services/processApi';
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

export default function ManageProcessesPage() {
  const { toast } = useToast();
  const [showBpmnEditor, setShowBpmnEditor] = useState(false);
  const [selectedProcess, setSelectedProcess] = useState<Process | null>(null);
  const [processName, setProcessName] = useState('New Process');
  const [isDirty, setIsDirty] = useState(false);
  const [initialXml, setInitialXml] = useState<string>('');
  
  // State for real data
  const [processes, setProcesses] = useState<Process[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Prevent duplicate fetches under React StrictMode by tracking last loaded tab
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
      const processesResponse = await processApiService.listProcesses();
      if (processesResponse.data) {
        setProcesses(processesResponse.data);
      } else if (processesResponse.error) {
        setProcesses([]);
        toast({
          type: 'foreground',
          title: 'Unable to reach backend or database. Please check your connection or try again later.'
        });
      }
    } catch (err) {
      setProcesses([]);
      toast({
        type: 'foreground',
        title: 'Unable to reach backend or database. Please check your connection or try again later.'
      });
      console.log('No processes found or error occurred:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNewProcess = () => {
    setProcessName('New Process');
    setSelectedProcess(null);
    setInitialXml('');
    setShowBpmnEditor(true);
  };

  const handleEditProcess = async (process: Process) => {
    try {
      // If the process doesn't have bpmn_xml (summary data), fetch the full process
      if (!process.bpmn_xml) {
        const processId = process.id || (process as any)._id || (process as any).process_id;
        if (!processId) {
          throw new Error('Cannot determine process ID to fetch full data');
        }
        
        const response = await processApiService.getProcess(processId);
        
        if (response.data) {
          setSelectedProcess(response.data);
          setProcessName(response.data.name);
          setInitialXml(response.data.bpmn_xml || '');
        } else {
          throw new Error(response.error || 'Failed to fetch process data');
        }
      } else {
        // Process already has bpmn_xml data
        setSelectedProcess(process);
        setProcessName(process.name);
        setInitialXml(process.bpmn_xml);
      }
      
      setShowBpmnEditor(true);
      setIsDirty(false);
    } catch (err) {
      toast({
        title: 'Error Loading Process',
        description: err instanceof Error ? err.message : 'Failed to load process data.',
        variant: 'destructive',
      });
    }
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
      if (selectedProcess) {
        // Update existing process
        const id = selectedProcess.id || (selectedProcess as any)._id || (selectedProcess as any).process_id;
        
        if (!id) {
          throw new Error('Cannot determine process ID for update');
        }

        const updateData: ProcessUpdate = {
          name: processName,
          description: `Process updated from BPMN editor`,
          bpmn_xml: xml,
          version: "1.0.0",
          category: "General",
          tags: ["bpmn", "workflow"],
          metadata: {},
        };

        const response = await processApiService.updateProcess(id, updateData);
        
        if (response.data) {
          toast({
            title: 'Success',
            description: 'Process updated successfully!',
          });
          setSelectedProcess(response.data);
        } else {
          throw new Error(response.error || 'Failed to update process');
        }
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

  const handleDeleteProcess = async (processOrId: string | Process) => {
    // Resolve ID from either a string id or a Process object (fall back to common fields)
    const id = typeof processOrId === 'string'
      ? processOrId
      : (processOrId.id || (processOrId as any)._id || (processOrId as any).process_id);

    if (!id) {
      toast({
        title: 'Error',
        description: 'Cannot determine process id for deletion.',
        variant: 'destructive',
      });
      return;
    }

    if (confirm('Are you sure you want to delete this process?')) {
      try {
        const response = await processApiService.deleteProcess(id);
        if (response.data) {
          toast({
            title: 'Success',
            description: 'Process deleted successfully!',
          });
          loadData(); // Refresh the list
        } else {
          toast({
            title: 'Error',
            description: `Failed to delete process: ${response.error}`,
            variant: 'destructive',
          });
        }
      } catch (err) {
        toast({
          title: 'Error',
          description: `Error deleting process: ${err instanceof Error ? err.message : 'Unknown error'}`,
          variant: 'destructive',
        });
      }
    }
  };

  const handleConvertToTemplate = async (process: Process) => {
    try {
      const templateData = {
        name: `${process.name} Template`,
        description: `Template created from ${process.name}`,
        bpmn_xml: process.bpmn_xml,
        process_id: `template_${Date.now()}`,
        metadata: process.metadata,
        source_process_id: process.id
      };

      const response = await processApiService.createTemplateFromProcess(process.id, templateData);
      if (response.data) {
        toast({
          title: 'Success',
          description: 'Template created successfully!',
        });
        loadData(); // Refresh the list
      } else {
        toast({
          title: 'Error',
          description: `Failed to create template: ${response.error}`,
          variant: 'destructive',
        });
      }
    } catch (err) {
      toast({
        title: 'Error',
        description: `Error creating template: ${err instanceof Error ? err.message : 'Unknown error'}`,
        variant: 'destructive',
      });
    }
  };

  if (showBpmnEditor) {
    return (
      <AppShell title="Edit Process" subtitle="Modify business process">
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
              ← Back to Manage Processes
            </button>
          </div>
          <BpmnModelerComponent
            onSave={handleSaveProcess}
            onClose={() => setShowBpmnEditor(false)}
            autoCreateDiagram={!selectedProcess}
            initialXml={initialXml}
            onDirtyChange={setIsDirty}
            isDirty={isDirty}
          />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell title="Manage Processes" subtitle="Edit and manage business processes">
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-medium text-gray-900">Manage Processes</h3>
          <button
            onClick={handleCreateNewProcess}
            className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded flex items-center"
          >
            <PlusIcon className="mr-2 h-4 w-4" />
            New Process
          </button>
        </div>
        
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-500">Loading processes...</p>
          </div>
        ) : error ? (
          <div className="text-center py-8 space-y-2">
            <p className="text-red-500">{error}</p>
            {(process.env.NEXT_PUBLIC_BPMN_OFFLINE_MODE === 'true' || /offline|connrefused|failed to fetch/i.test(error)) && (
              <p className="text-xs text-gray-500">Backend unreachable (offline mode). Showing empty list.</p>
            )}
          </div>
        ) : processes.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500">No processes found. Create your first process to get started.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {processes.map((process, idx) => (
                  <tr key={process.id || process.process_id || `${process.name}-${idx}` }>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => handleEditProcess(process)}
                        className="text-blue-600 hover:text-blue-700 underline"
                      >
                        {process.name}
                      </button>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{process.description}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        process.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {process.status === 'active' ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                      <button
                        onClick={() => handleConvertToTemplate(process)}
                        className="text-blue-600 hover:text-blue-900"
                        title="Convert to Template"
                      >
                        <DocumentIcon className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteProcess(process)}
                        className="text-red-600 hover:text-red-900"
                        title="Delete Process"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </AppShell>
  );
}
