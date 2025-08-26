"use client"

import React from 'react';
import { AppShell } from '@/components/app-shell';
import WorkingBpmnModeler from '@/components/modelling/working-bpmn-modeler';

// Render the lightweight, dependency-free BPMN modeler immediately to avoid any
// spinner/blocked state from heavy dynamic imports or SSR.
export default function ModellingPage() {
  const handleSaveWorkflow = async (xml: string, _svg?: string) => {
    try {
      const processEngineUrl = process.env.NEXT_PUBLIC_PROCESS_ENGINE_URL || 'http://localhost:8090';
      const response = await fetch(`${processEngineUrl}/workflows`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: `Workflow_${Date.now()}`,
          version: '1.0',
          bpmn_xml: xml,
          description: 'Workflow created via WFM App',
        }),
      });

      if (!response.ok) throw new Error('Failed to save workflow');
      const result = await response.json();
      alert(`Workflow saved successfully! ID: ${result.id}`);
    } catch (error) {
      console.error('Error saving workflow:', error);
      alert('Failed to save workflow. Please try again.');
    }
  };

  return (
    <AppShell title="BPMN Workflow Editor" subtitle="Create and edit BPMN workflows">
      <WorkingBpmnModeler onSave={handleSaveWorkflow} />
    </AppShell>
  );
}
