This is a new requirement. When we create a BPMN process, we need to execute it and store the workflow instance in the database. The workflow instance should include the following information:  
    1. The workflow instance id
    2. The workflow instance name
    3. The workflow instance description
    4. The workflow instance created at
    5. The workflow instance updated at
    6. The workflow instance created by
    7. The workflow instance updated by
    8. The workflow instance status

2. The workflow engine executes the process tasks. If an error occurs, the workflow instance should be updated with the error message. All errors should gracefully logged in the execution logs and show a toast notification to the user instead of abruptly stopping the workflow and application.
3. The workflow instance should be updated with the completed status when the process is completed.
4. The workflow instance should be updated with the failed status when the process is failed.
5. The workflow instance should be updated with the cancelled status when the process is cancelled.
6. The workflow instance should be updated with the suspended status when the process is suspended.
7. The workflow instance should be updated with the resumed status when the process is resumed.
8. The workflow instance should be updated with the timeout status when the process is timed out.
9. The workflow instance should be updated with the aborted status when the process is aborted.
10. The workflow instance should be updated with the paused status when the process is paused.

11. The execution engine of the BPMN is SpiffWorkflow in wfmProcess.
12. The workflow instance details are stored in the database in wfmServices. Please check.
13. The wfmApp app has Instances page which lists all the workflow instances. We need to have an API to get the workflow instances from the database and this page should display all the workflow instances with a link to the workflow instance details page.
14. Workflow instance details page will display all the steps in the workflow in a table and their status. Along with that, it should also show a page where it can render the BPMN diagram of the workflow with color coding.