Please refer to wsm-highlevel-architecture-v1.png and END_TO_END_API_SEQUENCE.md and UML_END_TO_END_FLOW.md for any references.

The existing code is good and intact. So, create a new branch in both the repos as below. Below are the changes that we need to make to wfmServices and intServices

wfmServices - new branch to be created: feature/new-flow
intServices - new branch to be created: feature/integrate-new-flow

1. In Online Mongo cloud, we have multiple documents for same entity - example - analyst and technician are the same. We can remove technician collection in the online mongo DB and correct the code to analyst if it is referring to technician anywhere.
2. Secondly, we will have to slightly change when the order is coming from any of the applications like OSM, Activation, etc, it will invoke http://localhost:8082/ingest/osm API in the intServices (integration layer), first the order has to be logged into orders collection. Then from orders, rules has to pick up the order that is in "READY" state and then start processing it. Once Rule decomposes the Order and identifies into tasks and schedule it as a job, which is existing flow. In the COMPLETE_API_GUIDE.md, I see order_id in the Rules APIs - /rules POST API, but I am NOT seeing any reference where order_id is stored. This is where we need order service to maintain orders. Not sure if it needs to be in Order service or anywhere else. So, please check and update accordingly.
3. I need a report, where I will pass the OrderId and I need what all jobs are associated with it and what all jobs are completed, pending, to be started, scheduled, what all jobs are assigned to analysts and what are not etc.
4. Please update the  END_TO_END_API_SEQUENCE.md and COMPLETE_API_GUIDE.md with relevant changes to API endpoints and request payloads.