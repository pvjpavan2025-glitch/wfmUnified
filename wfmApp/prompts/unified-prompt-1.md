Background contextual information:
1. Added another folder to the workspace called as "wfm". This folder has wfmApp and wfmServices and intServices. Below are the descriptions for each:
    a. wfmApp - is the UI
    b. wfmServices - is the backend intServices
    c. intServices - is the integration layer.
2. Refer to architecture diagram - wfm/references/wsm-highlevel-architecture-v1.png and wfm/wfmServices/prompts/UML_END_TO_END_FLOW.md for more details on the wfmApp.
3. All the Mongo, Redis DB details can be found in wfmServices/docker-compose.integrated.yml and we need to use these databases. If needed, please create a postgres database container as well.

Requirement:
1. Create a new branch feature/load-save-intg in both wfmProcess and wfm repos (and whenever necessary with the same branch name so that we can track it accordingly)
2. Requirement is that we need to integrate wfmProcess/frontend pages into wfmApp i.e., wfmApp is the main application. Now, we need to create a sidebar menu in that with name called 'Modelling'. If a user clicks that menu, then it should render those pages or redirect to that application. But that application should also have that sidebar as user should NOT know that we are moving to a different application.
3. Then move wfmServices/docker-compose.integrated.yml into the workspace level and update the docker compose file accordingly. Also, integrate this with wfmProcess/docker-compose.yml because both the applications have to be deployed as a single unit.