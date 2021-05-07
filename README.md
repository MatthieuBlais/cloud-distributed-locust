# cloud-distributed-locust

[Locust](https://github.com/locustio/locust): Locust is an easy to use, scriptable and scalable performance testing tool.

When testing an application with hundreds or thousands of users, you may need to execute locust in distributed mode. This is natively supported by Locust itself, however when it comes to run the nodes on remote servers, it's up-to-you to do the configuration. 

This repo helps to run Locust using Step Function, ECR, and Fargate. GCP support may come later.