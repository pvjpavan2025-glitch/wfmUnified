'use client'

import React, { useState } from 'react'
import BpmnModeler from './BpmnModeler'

/**
 * Test component for validating BPMN modeler canvas initialization
 * Used to prevent root-0 error regressions
 */
export default function BpmnModelerTest() {
  const [testScenario, setTestScenario] = useState<'empty' | 'withXml'>('empty')
  const [testKey, setTestKey] = useState(0)
  const [isDirty, setIsDirty] = useState(false)

  const sampleXml = `<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="Definitions_1" targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="Process_1" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1" />
    <bpmn:task id="Task_1" name="Sample Task" />
    <bpmn:endEvent id="EndEvent_1" />
    <bpmn:sequenceFlow id="Flow_1" sourceRef="StartEvent_1" targetRef="Task_1" />
    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_1" targetRef="EndEvent_1" />
  </bpmn:process>
  <bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Process_1">
      <bpmndi:BPMNShape id="_BPMNShape_StartEvent_2" bpmnElement="StartEvent_1">
        <dc:Bounds x="179" y="99" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Activity_1" bpmnElement="Task_1">
        <dc:Bounds x="270" y="77" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Event_1" bpmnElement="EndEvent_1">
        <dc:Bounds x="422" y="99" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="Flow_1_di" bpmnElement="Flow_1">
        <di:waypoint x="215" y="117" />
        <di:waypoint x="270" y="117" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_2_di" bpmnElement="Flow_2">
        <di:waypoint x="370" y="117" />
        <di:waypoint x="422" y="117" />
      </bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>`

  const resetTest = () => {
    setTestKey(prev => prev + 1)
  }

  return (
    <div className="p-4 space-y-4">
      <div className="bg-blue-50 p-4 rounded-lg">
        <h2 className="text-lg font-semibold mb-2">BPMN Modeler Test Suite</h2>
        <p className="text-sm text-gray-600 mb-4">
          This component tests canvas initialization to prevent root-0 error regressions.
        </p>
        
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => {
              setTestScenario('empty')
              resetTest()
            }}
            className={`px-4 py-2 rounded ${
              testScenario === 'empty' 
                ? 'bg-blue-500 text-white' 
                : 'bg-gray-200 text-gray-700'
            }`}
          >
            Test Empty Diagram
          </button>
          <button
            onClick={() => {
              setTestScenario('withXml')
              resetTest()
            }}
            className={`px-4 py-2 rounded ${
              testScenario === 'withXml' 
                ? 'bg-blue-500 text-white' 
                : 'bg-gray-200 text-gray-700'
            }`}
          >
            Test with Sample XML
          </button>
          <button
            onClick={resetTest}
            className="px-4 py-2 bg-green-500 text-white rounded"
          >
            Reset Test
          </button>
        </div>

        <div className="text-sm">
          <strong>Current Test:</strong> {testScenario === 'empty' ? 'Empty diagram creation' : 'XML import with existing content'}
        </div>
      </div>

      <div className="border border-gray-300 rounded-lg" style={{ height: '600px' }}>
        <BpmnModeler
          key={testKey}
          initialXml={testScenario === 'withXml' ? sampleXml : undefined}
          onDirtyChange={setIsDirty}
          isDirty={isDirty}
          onSave={(xml: string) => {
            console.log('XML saved:', xml ? 'Has content' : 'Empty')
          }}
        />
      </div>

      <div className="bg-gray-50 p-4 rounded-lg text-sm">
        <h3 className="font-semibold mb-2">Test Instructions:</h3>
        <ul className="space-y-1">
          <li>• <strong>Empty Diagram Test:</strong> Should create a new diagram without errors</li>
          <li>• <strong>XML Import Test:</strong> Should load existing content without canvas errors</li>
          <li>• <strong>Reset Test:</strong> Should reinitialize cleanly without root-0 errors</li>
          <li>• <strong>Check Console:</strong> No "Canvas layers not properly initialized" errors should appear</li>
        </ul>
      </div>
    </div>
  )
}
