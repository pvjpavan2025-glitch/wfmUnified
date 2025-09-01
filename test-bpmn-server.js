const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 3081;

// Read BPMN files from the documentation folder
const loadBpmnFile = (fileName) => {
  try {
    const filePath = path.join(__dirname, 'documentation', 'bpmn-samples', fileName);
    return fs.readFileSync(filePath, 'utf8');
  } catch (error) {
    console.log(`Could not load ${fileName}, using fallback`);
    return null;
  }
};

// Load actual BPMN files
const telecomO2A = loadBpmnFile('telecom-o2a.xml');
const telecomO2ACamunda = loadBpmnFile('telecom-o2a-camunda.xml');

// Sample BPMN XML content
const sampleBpmn = `<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                  xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
                  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
                  xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
                  id="Definitions_1"
                  targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="SupplyChainInventoryReplenishment" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1" name="Inventory Low">
      <bpmn:outgoing>Flow_1</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:sequenceFlow id="Flow_1" sourceRef="StartEvent_1" targetRef="Task_CheckInventory" />
    
    <bpmn:task id="Task_CheckInventory" name="Check Current Inventory Levels">
      <bpmn:incoming>Flow_1</bpmn:incoming>
      <bpmn:outgoing>Flow_2</bpmn:outgoing>
    </bpmn:task>
    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_CheckInventory" targetRef="Gateway_1" />
    
    <bpmn:exclusiveGateway id="Gateway_1" name="Stock Level?">
      <bpmn:incoming>Flow_2</bpmn:incoming>
      <bpmn:outgoing>Flow_3</bpmn:outgoing>
      <bpmn:outgoing>Flow_4</bpmn:outgoing>
    </bpmn:exclusiveGateway>
    
    <bpmn:sequenceFlow id="Flow_3" name="Critical" sourceRef="Gateway_1" targetRef="Task_UrgentOrder" />
    <bpmn:sequenceFlow id="Flow_4" name="Low" sourceRef="Gateway_1" targetRef="Task_RegularOrder" />
    
    <bpmn:task id="Task_UrgentOrder" name="Place Urgent Replenishment Order">
      <bpmn:incoming>Flow_3</bpmn:incoming>
      <bpmn:outgoing>Flow_5</bpmn:outgoing>
    </bpmn:task>
    
    <bpmn:task id="Task_RegularOrder" name="Place Regular Replenishment Order">
      <bpmn:incoming>Flow_4</bpmn:incoming>
      <bpmn:outgoing>Flow_6</bpmn:outgoing>
    </bpmn:task>
    
    <bpmn:sequenceFlow id="Flow_5" sourceRef="Task_UrgentOrder" targetRef="Task_ReceiveGoods" />
    <bpmn:sequenceFlow id="Flow_6" sourceRef="Task_RegularOrder" targetRef="Task_ReceiveGoods" />
    
    <bpmn:task id="Task_ReceiveGoods" name="Receive and Update Inventory">
      <bpmn:incoming>Flow_5</bpmn:incoming>
      <bpmn:incoming>Flow_6</bpmn:incoming>
      <bpmn:outgoing>Flow_7</bpmn:outgoing>
    </bpmn:task>
    
    <bpmn:sequenceFlow id="Flow_7" sourceRef="Task_ReceiveGoods" targetRef="EndEvent_1" />
    
    <bpmn:endEvent id="EndEvent_1" name="Inventory Replenished">
      <bpmn:incoming>Flow_7</bpmn:incoming>
    </bpmn:endEvent>
  </bpmn:process>
  
  <bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="SupplyChainInventoryReplenishment">
      <bpmndi:BPMNShape id="_BPMNShape_StartEvent_2" bpmnElement="StartEvent_1">
        <dc:Bounds x="179" y="99" width="36" height="36" />
        <bpmndi:BPMNLabel>
          <dc:Bounds x="166" y="142" width="63" height="14" />
        </bpmndi:BPMNLabel>
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Task_CheckInventory_di" bpmnElement="Task_CheckInventory">
        <dc:Bounds x="270" y="77" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Gateway_1_di" bpmnElement="Gateway_1" isMarkerVisible="true">
        <dc:Bounds x="425" y="92" width="50" height="50" />
        <bpmndi:BPMNLabel>
          <dc:Bounds x="485" y="110" width="63" height="14" />
        </bpmndi:BPMNLabel>
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Task_UrgentOrder_di" bpmnElement="Task_UrgentOrder">
        <dc:Bounds x="530" y="37" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Task_RegularOrder_di" bpmnElement="Task_RegularOrder">
        <dc:Bounds x="530" y="147" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Task_ReceiveGoods_di" bpmnElement="Task_ReceiveGoods">
        <dc:Bounds x="690" y="77" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="EndEvent_1_di" bpmnElement="EndEvent_1">
        <dc:Bounds x="852" y="99" width="36" height="36" />
        <bpmndi:BPMNLabel>
          <dc:Bounds x="833" y="142" width="75" height="27" />
        </bpmndi:BPMNLabel>
      </bpmndi:BPMNShape>
      
      <bpmndi:BPMNEdge id="Flow_1_di" bpmnElement="Flow_1">
        <di:waypoint x="215" y="117" />
        <di:waypoint x="270" y="117" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_2_di" bpmnElement="Flow_2">
        <di:waypoint x="370" y="117" />
        <di:waypoint x="425" y="117" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_3_di" bpmnElement="Flow_3">
        <di:waypoint x="450" y="92" />
        <di:waypoint x="450" y="77" />
        <di:waypoint x="530" y="77" />
        <bpmndi:BPMNLabel>
          <dc:Bounds x="462" y="59" width="35" height="14" />
        </bpmndi:BPMNLabel>
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_4_di" bpmnElement="Flow_4">
        <di:waypoint x="450" y="142" />
        <di:waypoint x="450" y="187" />
        <di:waypoint x="530" y="187" />
        <bpmndi:BPMNLabel>
          <dc:Bounds x="475" y="193" width="21" height="14" />
        </bpmndi:BPMNLabel>
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_5_di" bpmnElement="Flow_5">
        <di:waypoint x="630" y="77" />
        <di:waypoint x="660" y="77" />
        <di:waypoint x="660" y="117" />
        <di:waypoint x="690" y="117" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_6_di" bpmnElement="Flow_6">
        <di:waypoint x="630" y="187" />
        <di:waypoint x="660" y="187" />
        <di:waypoint x="660" y="117" />
        <di:waypoint x="690" y="117" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_7_di" bpmnElement="Flow_7">
        <di:waypoint x="790" y="117" />
        <di:waypoint x="852" y="117" />
      </bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>`;

const server = http.createServer((req, res) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.url}`);
  
  // Handle preflight requests
  if (req.method === 'OPTIONS') {
    res.writeHead(200, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization, Accept',
      'Access-Control-Max-Age': '3600'
    });
    res.end();
    return;
  }

  // Serve BPMN files with CORS headers
  if (req.url === '/supplychain-inventory-replinishment.xml' || req.url === '/sample.bpmn') {
    res.writeHead(200, {
      'Content-Type': 'application/xml',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Cache-Control': 'no-cache'
    });
    res.end(sampleBpmn);
    return;
  }

  // Serve actual BPMN files from documentation
  if (req.url === '/telecom-o2a.xml' && telecomO2A) {
    res.writeHead(200, {
      'Content-Type': 'application/xml',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Cache-Control': 'no-cache'
    });
    res.end(telecomO2A);
    return;
  }

  if (req.url === '/telecom-o2a-camunda.xml' && telecomO2ACamunda) {
    res.writeHead(200, {
      'Content-Type': 'application/xml',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Cache-Control': 'no-cache'
    });
    res.end(telecomO2ACamunda);
    return;
  }

  // Default 404 response
  res.writeHead(404, {
    'Content-Type': 'text/plain',
    'Access-Control-Allow-Origin': '*'
  });
  res.end('File not found. Available files:\n' +
          '- /supplychain-inventory-replinishment.xml\n' +
          '- /sample.bpmn\n' +
          '- /telecom-o2a.xml\n' +
          '- /telecom-o2a-camunda.xml');
});

server.listen(PORT, () => {
  console.log(`BPMN file server running on http://localhost:${PORT}`);
  console.log('Available files:');
  console.log('  - http://localhost:3081/supplychain-inventory-replinishment.xml');
  console.log('  - http://localhost:3081/sample.bpmn');
  console.log('  - http://localhost:3081/telecom-o2a.xml');
  console.log('  - http://localhost:3081/telecom-o2a-camunda.xml');
  console.log('');
  console.log('Press Ctrl+C to stop the server');
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n\nShutting down BPMN file server...');
  server.close(() => {
    console.log('Server stopped.');
    process.exit(0);
  });
});
