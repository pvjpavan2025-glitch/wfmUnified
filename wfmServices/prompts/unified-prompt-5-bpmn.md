This is a new requirement. So, please create a new branch feature/modelling-integration

Requirements:
1. We have modelling side menu. On clicking on it, we are launching BPMN process editor. Please check the screenshot.
2. I want a submenu to Modelling as "New Process", "Manage Processes", "Instances", "Templates"
    i. New Process: 
        a. This will launch the BPMN process editor. 
        b. Currently, we DONT have an option to save the process into any Database. So, we need to save it in the local database and retrive from the same.
        c. User can also create a process from scratch or from a template. So, we need to have a button to "create from scratch" and "create from template".
    ii. Manage Processes: This will list all the processes. We need to show the process name, description, created date, last modified date, status, etc in a table and a button to "edit"/"delete"/"convert to template" the process.
    iii. Instances: This will list all the instances i.e., process executions.
    iv. Templates: This will list all the templates - currently, there is no provision for template. So, when we click on New process, we need a button to save it as template. Similarly, when we click on Manage Processes, we need a button to save it as template. Template should be stored as a separate collection/table in the database.

Context:
1. Currently, we have wfmProcess folder in which we have backend and SpiffWorkflow folders. Check the logic here and update the same. Also, update relevant files in the frontend (wfmApp folder).
2. For your context, SpiffWorkflow is storing data in Postgres and we are using MongoDB. So, we need to update the logic to store data in MongoDB (OR) have a pointer/context to save relevant data in either databases.
3. We have backend BPMN APIs at http://localhost:8100/docs#/

Please make sure you first draft the TODOs and have a clear cut plan before you start working on it. Also, please update the TODOs in the README.md file and Summary in the README.md file once you are done with the work. Prompt me for any clarification.

