Create a new branch feature/azurePipelines 

Create Azure Pipelines in wfmInfra. 

Pipelines should take the code from main branch or any other branch as parameter

Then it should checkout the code and build docker containers for all the services including wfmServices, wfmApp, intServices and wfmProcess.

Then deploy it to Docker Hub

Deploy the docker container into Azure Web Apps

Create an API Manager and point all the endpoints from wfmServices and wfmProcess/backend 

Make sure wfmApp is pointing to these API Manager API endpoints

Refer to RUN_PIPELINE_NOW.md and azure-pipelines-wfm.yml for details regarding Azure subscriptions, resourcegroups and other details.

Also, Mongo DB and Redis DB are in Mongo Atlas Cloud and Redis Cloud respectively. Please use them instead of Local mongo and local Redis

Similarly, for postgres, create a DB in Azure postgres and use that instead of postgres in docker.

FInally summarize and document the steps to deploy and running the pipeline and all the API Manager endpoints and the sample payloads.

Prompt and ask me if u need anything else.

@RUN_PIPELINE_NOW.md @azure-pipelines-wfm.yml 