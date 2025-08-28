# Azure DevOps Setup Guide

## Create the service connection (new UI)

- Connection type: Azure Resource Manager
- Identity type: App registration (automatic)
- Credential:
  - Prefer “Workload identity federation (Recommended)” if your org allows OIDC (no secrets to rotate).
  - If WIF isn’t available in your tenant, select “Secret” (creates a client secret on the app registration).
- Scope level: Subscription
- Subscription: pick the target subscription
- Resource group: optional (leave blank to grant access at subscription scope)
- Service Connection Name: wfm-azure-conn (or any name you prefer)
- Security: check “Grant access permission to all pipelines” (or you can authorize the specific pipeline later)
- Save

## Map to pipeline

- In `wfmInfra/azure-pipelines-wfm.yml`, set:
  - `variables.azureSubscription: 'wfm-azure-conn'` (or your chosen name)
- If your project requires authorization, run the pipeline once and click “Authorize” when prompted.
- More info: https://aka.ms/yamlauthz
