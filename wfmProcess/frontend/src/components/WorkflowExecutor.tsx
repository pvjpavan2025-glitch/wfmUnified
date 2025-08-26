import React, { useState } from 'react';

interface WorkflowExecutorProps {
  workflowXml: string;
  onClose: () => void;
}

interface WorkflowInstance {
  id: string;
  status: 'running' | 'completed' | 'failed' | 'paused';
  currentTask?: string;
  variables: Record<string, any>;
  startTime: Date;
  endTime?: Date;
}

const WorkflowExecutor: React.FC<WorkflowExecutorProps> = ({ workflowXml, onClose }) => {
  const [instances, setInstances] = useState<WorkflowInstance[]>([]);
  const [currentInstance, setCurrentInstance] = useState<WorkflowInstance | null>(null);
  const [variables, setVariables] = useState<Record<string, any>>({});
  const [isExecuting, setIsExecuting] = useState(false);

  const startWorkflow = async () => {
    if (!workflowXml) {
      alert('No workflow XML provided');
      return;
    }

    setIsExecuting(true);
    
    try {
      // Create a new workflow instance
      const newInstance: WorkflowInstance = {
        id: `instance_${Date.now()}`,
        status: 'running',
        currentTask: 'Start Event',
        variables: { ...variables },
        startTime: new Date()
      };

      setInstances(prev => [...prev, newInstance]);
      setCurrentInstance(newInstance);

      // Simulate workflow execution
      await simulateWorkflowExecution(newInstance);
      
    } catch (error) {
      console.error('Error starting workflow:', error);
      alert('Failed to start workflow');
    } finally {
      setIsExecuting(false);
    }
  };

  const simulateWorkflowExecution = async (instance: WorkflowInstance) => {
    // Simulate task execution with delays
    const tasks = ['Start Event', 'Sample Task', 'End Event'];
    
    for (let i = 0; i < tasks.length; i++) {
      const task = tasks[i];
      
      // Update current task
      setCurrentInstance(prev => prev ? { ...prev, currentTask: task } : null);
      
      // Simulate task processing time
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Update instance status
      if (i === tasks.length - 1) {
        // Last task completed
        setCurrentInstance(prev => prev ? { ...prev, status: 'completed', endTime: new Date() } : null);
        setInstances(prev => prev.map(inst => 
          inst.id === instance.id 
            ? { ...inst, status: 'completed', endTime: new Date() }
            : inst
        ));
      }
    }
  };

  const pauseWorkflow = () => {
    if (currentInstance) {
      setCurrentInstance(prev => prev ? { ...prev, status: 'paused' } : null);
      setInstances(prev => prev.map(inst => 
        inst.id === currentInstance.id 
          ? { ...inst, status: 'paused' }
          : inst
      ));
    }
  };

  const resumeWorkflow = () => {
    if (currentInstance && currentInstance.status === 'paused') {
      setCurrentInstance(prev => prev ? { ...prev, status: 'running' } : null);
      setInstances(prev => prev.map(inst => 
        inst.id === currentInstance.id 
          ? { ...inst, status: 'running' }
          : inst
      ));
      
      // Resume execution
      simulateWorkflowExecution(currentInstance);
    }
  };

  const stopWorkflow = () => {
    if (currentInstance) {
      setCurrentInstance(prev => prev ? { ...prev, status: 'failed', endTime: new Date() } : null);
      setInstances(prev => prev.map(inst => 
        inst.id === currentInstance.id 
          ? { ...inst, status: 'failed', endTime: new Date() }
          : inst
      ));
    }
  };

  const addVariable = () => {
    const key = prompt('Enter variable name:');
    const value = prompt('Enter variable value:');
    
    if (key && value !== null) {
      setVariables(prev => ({ ...prev, [key]: value }));
    }
  };

  const removeVariable = (key: string) => {
    setVariables(prev => {
      const newVars = { ...prev };
      delete newVars[key];
      return newVars;
    });
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4 flex justify-between items-center">
        <h2 className="text-xl font-semibold text-gray-900">Workflow Executor</h2>
        <div className="flex space-x-3">
          <button
            onClick={onClose}
            className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded text-sm font-medium"
          >
            Close
          </button>
        </div>
      </div>

      <div className="flex-1 flex">
        {/* Left Panel - Workflow Control */}
        <div className="w-96 bg-white border-r border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Workflow Control</h3>
          
          {/* Start Workflow */}
          <div className="mb-6">
            <button
              onClick={startWorkflow}
              disabled={isExecuting || !workflowXml}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-3 px-4 rounded"
            >
              {isExecuting ? 'Starting...' : 'Start Workflow'}
            </button>
          </div>

          {/* Current Instance Status */}
          {currentInstance && (
            <div className="mb-6 p-4 bg-blue-50 rounded-lg">
              <h4 className="font-medium text-blue-900 mb-2">Current Instance</h4>
              <div className="space-y-2 text-sm">
                <div><span className="font-medium">ID:</span> {currentInstance.id}</div>
                <div><span className="font-medium">Status:</span> 
                  <span className={`ml-2 px-2 py-1 rounded text-xs ${
                    currentInstance.status === 'running' ? 'bg-green-100 text-green-800' :
                    currentInstance.status === 'completed' ? 'bg-blue-100 text-blue-800' :
                    currentInstance.status === 'failed' ? 'bg-red-100 text-red-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    {currentInstance.status}
                  </span>
                </div>
                {currentInstance.currentTask && (
                  <div><span className="font-medium">Current Task:</span> {currentInstance.currentTask}</div>
                )}
                <div><span className="font-medium">Started:</span> {currentInstance.startTime.toLocaleTimeString()}</div>
                {currentInstance.endTime && (
                  <div><span className="font-medium">Ended:</span> {currentInstance.endTime.toLocaleTimeString()}</div>
                )}
              </div>
            </div>
          )}

          {/* Control Buttons */}
          {currentInstance && currentInstance.status === 'running' && (
            <div className="mb-6 space-y-2">
              <button
                onClick={pauseWorkflow}
                className="w-full bg-yellow-600 hover:bg-yellow-700 text-white font-medium py-2 px-4 rounded"
              >
                Pause Workflow
              </button>
              <button
                onClick={stopWorkflow}
                className="w-full bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded"
              >
                Stop Workflow
              </button>
            </div>
          )}

          {currentInstance && currentInstance.status === 'paused' && (
            <div className="mb-6">
              <button
                onClick={resumeWorkflow}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded"
              >
                Resume Workflow
              </button>
            </div>
          )}

          {/* Variables */}
          <div className="mb-6">
            <div className="flex justify-between items-center mb-2">
              <h4 className="font-medium text-gray-900">Variables</h4>
              <button
                onClick={addVariable}
                className="text-blue-600 hover:text-blue-700 text-sm"
              >
                + Add
              </button>
            </div>
            <div className="space-y-2">
              {Object.entries(variables).map(([key, value]) => (
                <div key={key} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                  <span className="text-sm">{key}: {value}</span>
                  <button
                    onClick={() => removeVariable(key)}
                    className="text-red-600 hover:text-red-700 text-xs"
                  >
                    ×
                  </button>
                </div>
              ))}
              {Object.keys(variables).length === 0 && (
                <p className="text-sm text-gray-500">No variables defined</p>
              )}
            </div>
          </div>
        </div>

        {/* Right Panel - Instance History */}
        <div className="flex-1 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Workflow Instances</h3>
          
          {instances.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-gray-400 mb-4">
                <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <p className="text-gray-500">No workflow instances yet</p>
              <p className="text-sm text-gray-400">Start a workflow to see execution history</p>
            </div>
          ) : (
            <div className="space-y-3">
              {instances.map((instance) => (
                <div key={instance.id} className="bg-white border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <span className="font-medium text-gray-900">{instance.id}</span>
                        <span className={`px-2 py-1 rounded text-xs ${
                          instance.status === 'running' ? 'bg-green-100 text-green-800' :
                          instance.status === 'completed' ? 'bg-blue-100 text-blue-800' :
                          instance.status === 'failed' ? 'bg-red-100 text-red-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {instance.status}
                        </span>
                      </div>
                      <div className="text-sm text-gray-600 space-y-1">
                        <div>Started: {instance.startTime.toLocaleString()}</div>
                        {instance.endTime && (
                          <div>Ended: {instance.endTime.toLocaleString()}</div>
                        )}
                        {instance.currentTask && (
                          <div>Current Task: {instance.currentTask}</div>
                        )}
                        {Object.keys(instance.variables).length > 0 && (
                          <div>Variables: {Object.keys(instance.variables).length}</div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WorkflowExecutor;
