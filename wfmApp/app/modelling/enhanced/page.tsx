"use client"

import React, { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { AppShell } from '@/components/app-shell';
import { 
  PlusIcon, 
  FolderIcon, 
  PlayIcon, 
  TemplateIcon,
  ChevronRightIcon,
  DocumentTextIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon
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

// Types are now imported from the API service

// State for real data
const [processes, setProcesses] = useState<Process[]>([]);
const [instances, setInstances] = useState<ProcessInstance[]>([]);
const [templates, setTemplates] = useState<Template[]>([]);
const [loading, setLoading] = useState(false);
const [error, setError] = useState<string | null>(null);

export default function EnhancedModellingPage() {
  const [activeTab, setActiveTab] = useState<'new-process' | 'manage-processes' | 'instances' | 'templates'>('new-process');
  const [showBpmnEditor, setShowBpmnEditor] = useState(false);
  const [selectedProcess, setSelectedProcess] = useState<Process | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);

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
          const processesResponse = await processApiService.listProcesses();
          if (processesResponse.data) {
            setProcesses(processesResponse.data.processes);
          } else if (processesResponse.error) {
            setError(processesResponse.error);
          }
          break;
          
        case 'instances':
          // For now, we'll load instances from all processes
          // In a real implementation, you might want to load instances differently
          const allInstances: ProcessInstance[] = [];
          const processesForInstances = await processApiService.listProcesses();
          if (processesForInstances.data) {
            for (const process of processesForInstances.data.processes) {
              const instancesResponse = await processApiService.listProcessInstances(process.id);
              if (instancesResponse.data) {
                allInstances.push(...instancesResponse.data.instances);
              }
            }
            setInstances(allInstances);
          }
          break;
          
        case 'templates':
          const templatesResponse = await processApiService.listTemplates();
          if (templatesResponse.data) {
            setTemplates(templatesResponse.data.templates);
          } else if (templatesResponse.error) {
            setError(templatesResponse.error);
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

  const handleCloseBpmnEditor = () => {
    setShowBpmnEditor(false);
    setSelectedTemplate(null);
  };

  const handleSaveProcess = async (xml: string) => {
    try {
      setLoading(true);
      
      // Create process data
      const processData: ProcessCreate = {
        name: selectedTemplate ? `Copy of ${selectedTemplate.name}` : 'New Process',
        description: selectedTemplate ? `Created from template: ${selectedTemplate.description}` : 'New process created in BPMN editor',
        bpmn_xml: xml,
        version: '1.0.0',
        category: selectedTemplate?.category || 'General',
        tags: selectedTemplate?.tags || [],
        created_by: 'current-user@company.com', // In real app, get from auth context
        tenant_id: 'default'
      };
      
      // Save to backend
      const response = await processApiService.createProcess(processData);
      
      if (response.data) {
        alert('Process saved successfully!');
        setShowBpmnEditor(false);
        // Refresh the processes list if we're on that tab
        if (activeTab === 'manage-processes') {
          loadData();
        }
      } else if (response.error) {
        alert(`Failed to save process: ${response.error}`);
      }
    } catch (err) {
      alert(`Error saving process: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleEditProcess = (process: Process) => {
    setSelectedProcess(process);
    setShowBpmnEditor(true);
  };

  const handleDeleteProcess = async (processId: string) => {
    if (confirm('Are you sure you want to delete this process?')) {
      try {
        setLoading(true);
        const response = await processApiService.deleteProcess(processId);
        
        if (response.data) {
          alert('Process deleted successfully!');
          // Refresh the processes list
          loadData();
        } else if (response.error) {
          alert(`Failed to delete process: ${response.error}`);
        }
      } catch (err) {
        alert(`Error deleting process: ${err instanceof Error ? err.message : 'Unknown error'}`);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleConvertToTemplate = async (process: Process) => {
    try {
      setLoading(true);
      const response = await processApiService.createTemplateFromProcess(process.id, {
        name: `${process.name} Template`,
        description: `Template created from process: ${process.description}`,
        category: process.category
      });
      
      if (response.data) {
        alert('Template created successfully!');
        // Refresh the templates list
        if (activeTab === 'templates') {
          loadData();
        }
      } else if (response.error) {
        alert(`Failed to create template: ${response.error}`);
      }
    } catch (err) {
      alert(`Error creating template: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'inactive':
        return 'bg-gray-100 text-gray-800';
      case 'draft':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getInstanceStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'paused':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (showBpmnEditor) {
    return (
      <AppShell title="BPMN Editor" subtitle={selectedTemplate ? `Creating from template: ${selectedTemplate.name}` : "Create New Process"}>
        <BpmnModelerComponent
          onSave={handleSaveProcess}
          onClose={handleCloseBpmnEditor}
        />
      </AppShell>
    );
  }

  return (
    <AppShell title="Process Modelling" subtitle="Design, manage, and execute BPMN workflows">
      <div className="bg-white shadow rounded-lg">
        {/* Navigation Tabs */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8 px-6" aria-label="Tabs">
            <button
              onClick={() => setActiveTab('new-process')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'new-process'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <PlusIcon className="w-5 h-5 inline mr-2" />
              New Process
            </button>
            <button
              onClick={() => setActiveTab('manage-processes')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'manage-processes'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <FolderIcon className="w-5 h-5 inline mr-2" />
              Manage Processes
            </button>
            <button
              onClick={() => setActiveTab('instances')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'instances'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <PlayIcon className="w-5 h-5 inline mr-2" />
              Instances
            </button>
            <button
              onClick={() => setActiveTab('templates')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'templates'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <TemplateIcon className="w-5 h-5 inline mr-2" />
              Templates
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {/* New Process Tab */}
          {activeTab === 'new-process' && (
            <div className="space-y-6">
              <div className="text-center">
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Create New Process
                </h3>
                <p className="text-gray-600 mb-6">
                  Design your business process using our BPMN editor
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Create from scratch */}
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
                  <PlusIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                  <h4 className="text-lg font-medium text-gray-900 mb-2">
                    Start from Scratch
                  </h4>
                  <p className="text-gray-500 mb-4">
                    Create a new process diagram from the beginning
                  </p>
                  <button
                    onClick={handleCreateNewProcess}
                    className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded transition-colors"
                  >
                    Create New Process
                  </button>
                </div>

                {/* Create from template */}
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
                  <TemplateIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                  <h4 className="text-lg font-medium text-gray-900 mb-2">
                    Use Template
                  </h4>
                  <p className="text-gray-500 mb-4">
                    Start with a pre-built template and customize it
                  </p>
                  <button
                    onClick={() => setActiveTab('templates')}
                    className="bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-4 rounded transition-colors"
                  >
                    Browse Templates
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Manage Processes Tab */}
          {activeTab === 'manage-processes' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-medium text-gray-900">
                  Manage Processes
                </h3>
                <button
                  onClick={() => setActiveTab('new-process')}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded"
                >
                  <PlusIcon className="w-4 h-4 inline mr-2" />
                  New Process
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Process
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Category
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Tasks
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Last Modified
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {loading ? (
                      <tr>
                        <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                          Loading processes...
                        </td>
                      </tr>
                    ) : error ? (
                      <tr>
                        <td colSpan={6} className="px-6 py-4 text-center text-red-500">
                          Error: {error}
                        </td>
                      </tr>
                    ) : processes.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                          No processes found. Create your first process to get started.
                        </td>
                      </tr>
                    ) : (
                      processes.map((process) => (
                      <tr key={process.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">{process.name}</div>
                            <div className="text-sm text-gray-500">{process.description}</div>
                            <div className="text-xs text-gray-400">v{process.version}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {process.category}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(process.status)}`}>
                            {process.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {process.task_count} tasks
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(process.updated_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                          <button
                            onClick={() => handleEditProcess(process)}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleConvertToTemplate(process)}
                            className="text-green-600 hover:text-green-900"
                          >
                            Template
                          </button>
                          <button
                            onClick={() => handleDeleteProcess(process.id)}
                            className="text-red-600 hover:text-red-900"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Instances Tab */}
          {activeTab === 'instances' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-medium text-gray-900">
                  Process Instances
                </h3>
                <button
                  onClick={() => setActiveTab('new-process')}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded"
                >
                  <PlusIcon className="w-4 h-4 inline mr-2" />
                  New Process
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Instance
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Process
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Started
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Started By
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {loading ? (
                      <tr>
                        <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                          Loading instances...
                        </td>
                      </tr>
                    ) : error ? (
                      <tr>
                        <td colSpan={6} className="px-6 py-4 text-center text-red-500">
                          Error: {error}
                        </td>
                      </tr>
                    ) : instances.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                          No instances found.
                        </td>
                      </tr>
                    ) : (
                      instances.map((instance) => (
                        <tr key={instance.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">#{instance.id}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">{instance.process_name}</div>
                            <div className="text-xs text-gray-500">v{instance.process_version}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getInstanceStatusColor(instance.status)}`}>
                            {instance.status === 'running' && <ClockIcon className="w-3 h-3 mr-1" />}
                            {instance.status === 'completed' && <CheckCircleIcon className="w-3 h-3 mr-1" />}
                            {instance.status === 'failed' && <XCircleIcon className="w-3 h-3 mr-1" />}
                            {instance.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(instance.started_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {instance.started_by}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button className="text-blue-600 hover:text-blue-900">
                            View Details
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Templates Tab */}
          {activeTab === 'templates' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-medium text-gray-900">
                  Process Templates
                </h3>
                <button
                  onClick={() => setActiveTab('new-process')}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded"
                >
                  <PlusIcon className="w-4 h-4 inline mr-2" />
                  New Process
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {loading ? (
                  <div className="col-span-full text-center py-8 text-gray-500">
                    Loading templates...
                  </div>
                ) : error ? (
                  <div className="col-span-full text-center py-8 text-red-500">
                    Error: {error}
                  </div>
                ) : templates.length === 0 ? (
                  <div className="col-span-full text-center py-8 text-gray-500">
                    No templates found. Create your first template to get started.
                  </div>
                ) : (
                  templates.map((template) => (
                    <div key={template.id} className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between">
                      <TemplateIcon className="w-8 h-8 text-blue-600 mb-3" />
                      <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                        {template.category}
                      </span>
                    </div>
                    <h4 className="text-lg font-medium text-gray-900 mb-2">{template.name}</h4>
                    <p className="text-gray-600 text-sm mb-4">{template.description}</p>
                    <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                      <span>Used {template.usage_count} times</span>
                      <span>{new Date(template.created_at).toLocaleDateString()}</span>
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleCreateFromTemplate(template)}
                        className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded text-sm transition-colors"
                      >
                        Use Template
                      </button>
                      <button className="px-3 py-2 text-gray-600 hover:text-gray-900 border border-gray-300 rounded text-sm transition-colors">
                        Preview
                      </button>
                                            </div>
                      </div>
                    ))
                  )}
                </div>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
