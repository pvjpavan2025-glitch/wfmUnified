"use client"

import React, { useState } from 'react';
import { AppShell } from '@/components/app-shell';
import BpmnModelerComponent from '@/components/modelling/BpmnModeler';

export default function ModellingPage() {
  const [showModeler, setShowModeler] = useState(false);
  const [showBpmnEditor, setShowBpmnEditor] = useState(false);

  const handleGetStarted = () => {
    setShowModeler(true);
  };

  const handleCreateWorkflow = () => {
    setShowBpmnEditor(true);
  };

  const handleCloseBpmnEditor = () => {
    setShowBpmnEditor(false);
  };

  const handleSaveWorkflow = (xml: string) => {
    console.log('Workflow saved:', xml);
    // Here you would typically send the XML to your backend
    alert('Workflow saved successfully! Check console for XML content.');
  };

  if (showBpmnEditor) {
    return (
      <AppShell title="BPMN Workflow Editor" subtitle="Create and edit BPMN workflows">
        <BpmnModelerComponent
          onSave={handleSaveWorkflow}
          onClose={handleCloseBpmnEditor}
        />
      </AppShell>
    );
  }

  if (showModeler) {
    return (
      <AppShell title="BPMN Modeler" subtitle="Workflow management and modeling">
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-medium text-gray-900">
              BPMN Modeler
            </h2>
            <button
              onClick={() => setShowModeler(false)}
              className="text-gray-500 hover:text-gray-700 text-sm"
            >
              ← Back to Home
            </button>
          </div>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
            <div className="text-gray-500 mb-4">
              <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Create New BPMN Workflow
            </h3>
            <p className="text-gray-500 mb-4">
              Start building your workflow by creating a new BPMN diagram
            </p>
            <button 
              onClick={handleCreateWorkflow}
              className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded"
            >
              Create New Workflow
            </button>
          </div>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell title="BPMN Workflow Engine" subtitle="Business Process Model and Notation">
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">
          Welcome to BPMN Workflow Engine
        </h2>
        <p className="text-gray-600 mb-4">
          This is a modern, cloud-native BPMN workflow execution engine integrated into your workforce management system.
        </p>
        <div className="mt-4">
          <button 
            onClick={handleGetStarted}
            className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded"
          >
            Get Started
          </button>
        </div>
      </div>
    </AppShell>
  );
}
