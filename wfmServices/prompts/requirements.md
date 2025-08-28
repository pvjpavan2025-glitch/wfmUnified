<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# convert this excel file to Markdown file as it is with tables and columns.

Here is your provided Excel file content **faithfully converted to Markdown format**. All tables, columns, and textual structure are maintained as in the original, using Markdown syntax.

## **Overall Requirements**

Our application name is **Workforce Management** or **WFM** in short.

- Need multiple services with authentication, security, and following SOLID Principles for below requirements.
- All the services are multi-tenant and we should be able to onboard any number of customers.
- All services should be scalable, which can auto-scale based on the load.
- When we onboard a new customer, tenantID should be part of every document and table that we are creating.


### **Service Requirements Table**

| Service | Component | Requirement | Expected Result |
| :-- | :-- | :-- | :-- |
| Rules Service (or Rules Engine) | Rules | Are a combination of Rules, Decomposer and Recogniser components. The Rules Service is the starting point of Workforce Management Application and this service entry point is exposed as an API | Any application or integration layer outside this application should invoke the Rules Engine API to start the process. |
|  |  | The input to Rules Engine is an "Order", which can be a rule or set of rules. | We should be able to manage all the rules using the Order ID, for a given tenant. |
|  |  | Users can create an order outside WFM, which can be sent to WFM's Rules API. The order can have multiple rules based on matching tag name or regular expressions | Rules Engine should be able to identify the rule or all the rules (using a RuleID) for a given order, for a given tenant and should be able to alter the sequence of rules as well. |
|  |  | Apart from Incoming rules, rules-admin user can also create additional rules in an order |  |
|  |  | External Applications should be able to create rules using REST API. So, creation and managing rules should be exposed as REST APIs | We should be able to view, create, update, delete, find rules using APIs and UI. |
|  | Decomposition | Decomposition service will break the rules (if more than 1 rule) and the sequence of rules and would pass the same to Process Identifier | Divide the rules using the tag name or regular expression. Outcome of this will be list of rules with all the metadata (ruleid, tenant id, rule itself, sequence, orderid). |
|  | Process Recognizer | Based on the number of rules, we need to identify which all processes to be invoked using this component. | The input to each process is the meta data (ruleid, tenant id, rule itself, sequence, orderid) and outcome should be process (or list of processes) and the list of tasks inside that process to be scheduled. |
| Intelligent Scheduler | Scheduler | Should be able to schedule a process based on analyst skills, process name, analyst availability, priority and SLA, geography location, dependency on processes (i.e., one process can have dependency...) | Scheduler should be intelligent enough to schedule the task for a given process, for a given tenant and should be able to run that. Input is process's, rule's and task's metadata (IDs, details, etc.) |
|  | JobHandler | When the job is run, it actually handsover the job to ProcessManager and oversees each task status in the process. Once all the tasks are completed, process is marked completed and job is marked completed. |  |
|  |  | Each job can have multiple child jobs which corresponds to each task in the process. Once all the tasks are completed, which is all the child jobs are completed, parent job is marked as complete. |  |
|  |  | Each child job can have an issue associated or parent job itself can have an issue or dependency to get completed. |  |
| Issue Handler | IssueHandler | Will handle all the issues raised for a job, task, process and tenant. Will have priority and SLA. Should be owned by an analyst or user or admin to mark the issue fixed or dependency completed. |  |
| Report and Analytics | Analytics | Should be able to get a report on how many tasks are pending per process, how many process are in running, completed, to be started, halted with issues per tenant and for all tenants. ... | Should be able to get list of all issues and their dependencies, ownership, SLA, pending duration, order status per application, per tenant and overall. |
|  | Reports | Should have APIs to extract the analytics and show on the UI / Reports |  |
| Security | Authorization and Authentication | All APIs should be authenticated and authorized using roles and JWT tokens. Only relevant data should be shown to respective user. One tenant user should not be able to see other tenants' data. |  |

This Markdown version is a direct conversion of your Excel file's relevant data for easy **viewing, sharing, or further documentation**.

<div style="text-align: center">⁂</div>

[^1]: wsm-requirements-v1.xlsx

