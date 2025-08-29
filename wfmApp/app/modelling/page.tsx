"use client"

import React, { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { AppShell } from '@/components/app-shell';
import { 
  PlusIcon, 
  FolderIcon, 
  PlayIcon, 
  DocumentIcon,
  ChevronRightIcon,
  DocumentTextIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  TrashIcon,
  PencilIcon
} from '@heroicons/react/24/outline';
import { processApiService, Process, ProcessInstance, Template, ProcessCreate } from '@/services/processApi';

// Dynamic imports for components
const BpmnModelerComponent = dynamic(
  () => import('@/components/modelling/BpmnModeler'),
  { 
    ssr: false,
    loading: () => <div className="flex items-center justify-center h-96">Loading BPMN Editor...</div>
  }
);

export default function ModellingPage() {
  const [activeTab, setActiveTab] = useState<'new-process' | 'manage-processes' | 'instances' | 'templates'>('new-process');
  const [showBpmnEditor, setShowBpmnEditor] = useState(false);
  const [selectedProcess, setSelectedProcess] = useState<Process | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  
  // State for real data
  const [processes, setProcesses] = useState<Process[]>([]);
  const [instances, setInstances] = useState<ProcessInstance[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load data when component mounts or tab changes
  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      switch (activeTab) {
        case 'manage-processes':
          try {
            const processesResponse = await processApiService.listProcesses();
            if (processesResponse.data) {
              setProcesses(processesResponse.data);
            } else if (processesResponse.error) {
              setError(processesResponse.error);
            }
          } catch (err) {
            // If there's an error, just set empty processes instead of throwing
            setProcesses([]);
            console.log('No processes found or error occurred:', err);
          }
          break;
          
        case 'instances':
          try {
            // For now, we'll load instances from all processes
            const allInstances: ProcessInstance[] = [];
            const processesForInstances = await processApiService.listProcesses();
            if (processesForInstances.data) {
              for (const process of processesForInstances.data) {
                const instancesResponse = await processApiService.listProcessInstances(process.id);
                if (instancesResponse.data) {
                  allInstances.push(...instancesResponse.data);
                }
              }
            }
            setInstances(allInstances);
          } catch (err) {
            // If there's an error, just set empty instances instead of throwing
            setInstances([]);
            console.log('No instances found or error occurred:', err);
          }
          break;
          
        case 'templates':
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
          }
          break;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNewProcess = () => {
    setShowBpmnEditor(true);
  };

  const handleCreateFromTemplate = (template: Template) => {
    setSelectedTemplate(template);
    setShowBpmnEditor(true);
  };

  const handleSaveProcess = async (xml: string) => {
    try {
      // Prompt user for process name
      const processName = prompt('Enter process name:');
      if (!processName) {
        alert('Process name is required');
        return;
      }

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
        alert('Process saved successfully!');
        setShowBpmnEditor(false);
        loadData(); // Refresh the list
      } else {
        alert(`Failed to save process: ${response.error}`);
      }
    } catch (err) {
      alert(`Error saving process: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleDeleteProcess = async (processId: string) => {
    if (confirm('Are you sure you want to delete this process?')) {
      try {
        const response = await processApiService.deleteProcess(processId);
        if (response.data) {
          alert('Process deleted successfully!');
          loadData(); // Refresh the list
        } else {
          alert(`Failed to delete process: ${response.error}`);
        }
      } catch (err) {
        alert(`Error deleting process: ${err instanceof Error ? err.message : 'Unknown error'}`);
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
        alert('Template created successfully!');
        loadData(); // Refresh the list
      } else {
        alert(`Failed to create template: ${response.error}`);
      }
    } catch (err) {
      alert(`Error creating template: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  if (showBpmnEditor) {
    return (
      <AppShell title="BPMN Editor" subtitle="Create or edit BPMN process">
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-medium text-gray-900">
              {selectedTemplate ? 'Create Process from Template' : 'Create New Process'}
            </h2>
            <button
              onClick={() => setShowBpmnEditor(false)}
              className="text-gray-500 hover:text-gray-700 text-sm"
            >
              ← Back to Modelling
            </button>
          </div>
          <BpmnModelerComponent
            onSave={handleSaveProcess}
            onClose={() => setShowBpmnEditor(false)}
          />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell title="Modelling" subtitle="BPMN Process Management">
      <div className="flex h-full">
        {/* Side Menu */}
        <div className="w-64 bg-gray-50 border-r border-gray-200 p-4">
          <nav className="space-y-2">
            <button
              onClick={() => setActiveTab('new-process')}
              className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                activeTab === 'new-process'
                  ? 'bg-blue-100 text-blue-700 border border-blue-200'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
              }`}
            >
              <PlusIcon className="mr-3 h-5 w-5" />
              New Process
            </button>
            
            <button
              onClick={() => setActiveTab('manage-processes')}
              className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                activeTab === 'manage-processes'
                  ? 'bg-blue-100 text-blue-700 border border-blue-200'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
              }`}
            >
              <FolderIcon className="mr-3 h-5 w-5" />
              Manage Processes
            </button>
            
            <button
              onClick={() => setActiveTab('instances')}
              className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                activeTab === 'instances'
                  ? 'bg-green-100 text-green-700 border border-green-200'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
              }`}
            >
              <PlayIcon className="mr-3 h-5 w-5" />
              Instances
            </button>
            
            <button
              onClick={() => setActiveTab('templates')}
              className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                activeTab === 'templates'
                  ? 'bg-blue-100 text-blue-700 border border-blue-200'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
              }`}
            >
              <DocumentIcon className="mr-3 h-5 w-5" />
              Templates
            </button>
          </nav>
        </div>

        {/* Main Content */}
        <div className="flex-1 p-6">
          {/* New Process Tab */}
          {activeTab === 'new-process' && (
            <div className="bg-white shadow rounded-lg p-6">
              <div className="text-center">
                <div className="text-gray-500 mb-4">
                  <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Create New BPMN Process
                </h3>
                <p className="text-gray-500 mb-6">
                  Start building your process by creating a new BPMN diagram from scratch or use an existing template
                </p>
                <div className="space-x-4">
                  <button 
                    onClick={handleCreateNewProcess}
                    className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded"
                  >
                    Create from Scratch
                  </button>
                  <button 
                    onClick={() => setActiveTab('templates')}
                    className="bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded"
                  >
                    Use Template
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Manage Processes Tab */}
          {activeTab === 'manage-processes' && (
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
                <div className="text-center py-8">
                  <p className="text-red-500">{error}</p>
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
                      {processes.map((process) => (
                        <tr key={process.id}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{process.name}</td>
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
                              onClick={() => handleDeleteProcess(process.id)}
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
          )}

          {/* Instances Tab */}
          {activeTab === 'instances' && (
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-6">Process Instances</h3>
              
              {loading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-2 text-gray-500">Loading instances...</p>
                </div>
              ) : error ? (
                <div className="text-center py-8">
                  <p className="text-red-500">{error}</p>
                </div>
              ) : instances.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-gray-500">No process instances found.</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Instance ID</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Process Name</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Started At</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {instances.map((instance) => (
                        <tr key={instance.id}>
                                                     <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{instance.id}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{instance.process_name}</td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              instance.status === 'completed' ? 'bg-green-100 text-green-800' :
                              instance.status === 'running' ? 'bg-blue-100 text-blue-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {instance.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {new Date(instance.started_at).toLocaleDateString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Templates Tab */}
          {activeTab === 'templates' && (
            <div className="bg-white shadow rounded-lg p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-medium text-gray-900">Templates</h3>
                <button
                  onClick={() => setActiveTab('manage-processes')}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded"
                >
                  Create from Process
                </button>
              </div>
              
              {loading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-2 text-gray-500">Loading templates...</p>
                </div>
              ) : error ? (
                <div className="text-center py-8">
                  <p className="text-red-500">{error}</p>
                </div>
              ) : templates.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-gray-500">No templates found. Create templates from existing processes.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {templates.map((template) => (
                    <div key={template.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
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
          )}
        </div>
      </div>
    </AppShell>
  );
}
