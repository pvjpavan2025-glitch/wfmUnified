Background contextual information:
1. WFM stands for Workforce Management similar to Service Now's WFM. We need to build similar application for Telecom domain.
2. In the workspace, we have a unified application with below structure:
    a. wfmApp - is the UI where Admin, technician, vendors login
    b. wfmServices - is the backend microservices for wfmApp including BFFs.
    c. intServices - is the integration layer for external services that can talk to wfmApp.
    d. wfmProcess - is the app for modelling a process and its workflow engine
    e. wfmInfra - we need to save all the scripts for both local and cloud deployment in this folder. Currently, all the scripts are moved to oldcode sub-directory in this folder. Refer to WFM_AZURE_DEPLOYMENT_GUIDE.md, WFM_PIPELINE_SUMMARY.md, verify-pipeline-readiness.sh, azure-pipelines-wfm.yml for deployment of wfmApp, wfmServices and intServices. We also need to include wfmProcess in the deployment.
2. Refer to architecture diagram - wfm/references/wsm-highlevel-architecture-v1.png and wfm/wfmServices/prompts/UML_END_TO_END_FLOW.md for more details on the wfmApp.
3. All the Mongo, Redis DB details can be found in wfmServices/docker-compose.integrated.yml and we need to use these databases. If needed, please create a postgres database container as well for wfmProcess.

Requirement:
1. Create a new branch feature/load-save-intg in both wfmProcess and wfm repos (and whenever necessary with the same branch name so that we can track it accordingly)
2. Requirement is that we need to deploy this to Azure containers and I should be able to login to wfmApp and launch wfmProcess app from there.
3. Also, I need to run it locally.
4. wfmApp, wfmServices, intServices, wfmProcess should have 2 .env files - one for local and one for cloud.
5. wfmApp should have URLs pointing to cloud wfmServices and intServices if run on cloud and local wfmServices and intServices if run on local.
6. Suggest if we need to move wfmProcess/frontend to wfmApp.
7. Document the steps to deploy this to Azure containers and run it locally and document them to an MD file in the workspace
8. Document all the steps to an MD file in the workspace
9. Create a ToDO list and ensure all the tasks are completed
