This is a new requirement. Refactor the code to support this requirement in wfmApp, wfmServices, intServices, wfmProcess accordingly.

Background Context:
1. Refer to requirements.md in wfmServices/prompts (for backend and overall application) and requirements.md in intServices/prompts (for integration layer). Refer to wsm-highlevel-architecture-v1.png architecture diagram indocumentation folder for overall architecture and sample input (input-order.json) in documentation folder. We need to refactor this code. 
2. Follow the ARCHITECTURE.md in wfmServices/docs for the architecture that is currently developed.

Requirement:
1. Whatever that comes in to the WFM is an order. An order can span multiple processes. Each process can have multiple tasks. A process is a workflow i.e., a BPMN diagram.
2. A Task cannot exist by itself, it has to be part of a process. A process cannot be scheduled. Only tasks can be assigned or scheduled.
3. So, there should be an Order with one or more processes and each process should have one or more tasks.
4. As a user, I should be able to create an order, add processes to it, add tasks to each process, assign tasks to analysts, schedule tasks, and track the status of each task.
5. Also, an order can come via Rules service. Rules service should be able to identify which all processes to be invoked using this component. The input to each process is the meta data (ruleid, tenant id, rule itself, sequence, orderid) and outcome should be process (or list of processes) and the list of tasks inside that process to be scheduled. 
6. Currently, I dont see any mapping between Order, Process, Task. Please make the necessary changes to support this requirement.
7. Now, I also have to make sure each process, its current state, tasks inside it, tasks status is saved in the database and can be retrieved. Remember each process is a BPMN diagram. So, we need to save the BPMN diagram in the database and retrieve it when needed and the engine should be able to execute it. The engine is SpiffWorkflow which is inside wfmProcess.
8. Also, a technician cannot exist himself. He has to be part of a Vendor. Vendor can have multiple technicians whom he can onboard to the application (onboarding technicians is a different requirement, so let's not focus on that now. Assume we have couple of technicians av available with each vendor with multiple skills). So, we need to have link technicians with Vendors.
9. When we assign a task, we have to assign that to a technician + a lead (lead is a manager of the technician). We cannot assign it to technician alone.

Please make necessary changes with above requirement.
CREATE A new branch feature/OrderProcessTask and make necessary changes in that.