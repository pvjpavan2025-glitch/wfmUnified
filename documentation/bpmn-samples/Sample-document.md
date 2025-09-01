## BPMN Samples - Documentation

### Domain: Telecom Use-cases 
1. Service Order Fulfillment Process:
    - This BPMN workflow combines human tasks, script tasks (Python and JavaScript), sub-processes, service tasks, send/receive tasks, manual task, business rule task, call activity BPMN activities in a meaningful way. This sample demonstrates the journey from customer request to activation, approval, manual intervention, automated service and business rules execution, messaging, and error handling. All activities are integrated into a single workflow and formatted for direct import
    - This workflow includes
        - User task: Data validation and approval steps
        - Script tasks: Python (fee calculation) & JavaScript (email generation)
        - Sub-process: Data validation & approval, SIM activation
        - Service task: Provisioning and SIM activation, with retries and headers
        - Send/Receive task: Customer notification and customer acknowledgement
        - Manual task: Document check, error review
        - Business rule task: Offer eligibility
        - Call activity: Activation
        - Boundary event: Error handling and manual review
2. Order to Activate (O2A)
    - Customer places a service order (user task)
    - Validate customer data and credit check (sub-process with user tasks)
    - Apply business rules for eligibility and plan selection (business rule task)
    - Service provisioning via service task calling external APIs
    - Notify customer by send task and await acknowledgement (receive task)
    - Activation handled in call activity subprocess
    - Manual task for exceptions or escalations
3. Trouble to Resolve (T2R) - Incident Management
    - Trouble ticket logging by customer or technician (user task)
    - Automatic diagnosis and service task to query network status
    - Script task to prioritize and categorize issue (JavaScript)
    - Send notification to field engineer (send task)
    - Receive field engineer report (receive task)
    - Manual task for follow-up inspections
    - Business rules task to apply SLA rules and escalation
    - Call activity to raise change request or network repair subprocess
4. Customer Complaint to Solution
    - User task to log complaint
    - Script task to triage urgency and route complaint
    - Sub-process to investigate complaint including manual checking and user interviews
    - Service task to update customer records and system statuses
    - Business rule task to determine compensation eligibility
    - Send task notification with resolution details to customer
    - Receive customer confirmation
    - Call activity to escalate or close complaint
5. Complex Telecom Network Service Provisioning and Incident Management
    - Incorporates multiple subprocesses, gateways, boundary events, multi-instance tasks, service/script tasks, event handling, and escalations for realistic process automation:
        - Multiple subprocesses: Order Management, Network Configuration, Incident Management, and Customer Communication.
        - Parallel gateways for simultaneous tasks like provisioning and testing.
        - Event-based gateways for handling inbound network alarms and customer escalations.
        - Multi-instance user tasks for parallel manual validations.
        - Boundary error events for retry and manual intervention.
        - Business rule tasks for SLA and priority evaluation.
        - Service tasks invoking external APIs for provisioning, network testing, and incident reporting.
        - Call activities for invoking specialized subprocesses like SIM management, Fault Management.
        - Script tasks for automated calculations, status updates.
        - Receive and send tasks for asynchronous communication with customers and network management systems.
        - Escalation paths with timer events prompting escalation notifications.

### Domain: Supply Chain Use-cases

1. Purchase Order to Payment
    - User task to create purchase request
    - Business rule task to verify supplier contracts and compliance
    - Service task to send purchase order to supplier system
    - Receive task for supplier order acceptance
    - Sub-process for goods receipt with manual inspection tasks
    - Script task for invoice validation
    - Service task to initiate payment process
    - End event on payment complete
2. Inventory Replenishment Process
    - Service task to monitor stock levels periodically
    - Business rule task to evaluate reorder needs
    - User task to approve reorder
    - Service task to place order with supplier
    - Receive task for order confirmation
    - Sub-process for shipping and logistics coordination (multiple manual and service tasks)
    - Script task to update inventory system automatically
    - Send notification on replenishment completion
3. Order Fulfillment and Delivery
    - Receive order via receive task
    - User task for order validation and packaging preparation
    - Service task to arrange shipment
    - Sub-process for quality check with manual tasks
    - Script task to calculate shipping costs dynamically
    - Send task to notify customer of shipment details
    - Receive delivery confirmation
    - Business rule task for return or refund eligibility processing