Imagine you are Python developer, who follows SOLID principles deligently. Create a Python code which is modular, secure, REST API framework that can take input from multiple applications and convert/transform into Rules Input API.

intServices folder is the integration layer. So, create the code in this folder. Please refer to wsm-highlevel-architecture-v1.png attached image. We are now building the integration layer. 

In the integration layer, we will have an UI also, where we will add the Applications to integrate like OSM,BRM,Activation etc as shown in the image. Currently, we are building Integration Layer backend servies.

Now, for each application, we will have to ask for API endpoints. So, we need below APIs:

1. Application - CRUD APIs
2. APIs for each application - CRUD APIs

After the above APIs are done, we will try to simulate end to end with one of the APIs. To start with, we are integrating OSM now. So, we need to provide a REST POST endpoint, which will be invoked by OSM.

For REST POST endpoint, we will have to come up with an input payload. This payload is nothing but the payload which will connect to Rules API that is exposed. Please check #WFM_SYSTEM_COMPLETE.md for any context of wfmServices.
For API documentation, please check #API_DOCUMENTATION.md

Our integration layer is dynamic and should be able to connect to any application and it should be able to transform the incoming input (example input-order.json) to Rules API, from which the RUles will create Order and its related jobs.