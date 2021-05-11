# cloud-distributed-locust

[Locust](https://github.com/locustio/locust): Locust is an easy to use, scriptable and scalable performance testing tool.

When testing an application with hundreds or thousands of users, you may need to execute locust in distributed mode. This is natively supported by Locust itself, however when it comes to run the nodes on remote servers, it's up-to-you to do the configuration.

This repo helps to run Locust using Step Function, ECR, and Fargate. GCP support may come later.



## Overall solution on AWS

![Architecture](./aws/architecture.png)

**Fargate**: Serverless container platform. Deploy your dockers for Locust master and worker nodes.

**Step Function**: For orchestration. First, deploy the master node. Once ready, deploy the worker nodes.

**Lambda**: Python function to check the status of the master node and extract its IP address to allow worker nodes to connect.

**S3 bucket**: Staging area to fetch data required by your Locust tests


### Orchestration flow


![Orchestration](./aws/orchestration.png)


### Setting up

See [here](./aws/cloudformation/README.md) for setup.


### Sample Input

Sample input to trigger the Step :

```
{
  "JobDetails": {
    "ExecutionId": "ANY_RANDOM_ID",
    "ClusterName": "YOUR_FARGATE_CLUSTER",
    "TaskDefinition": "arn:aws:ecs:YOUR_REGION:YOUR_ACCOUNT_ID:task-definition/YOUR_TASK_NAME:1",
    "AwsRegion": "YOUR_REGION",
    "Subnets": [SUBNET_1, SUBNET_2],
    "SecurityGroups": [SECURITY_GROUP_TASKS_MUST_USE],
    "FamilyName": "YOUR_TASK_NAME",
    "MasterTaskName": "YOUR_TASK_NAME",
    "MasterCommand": [YOUR_MASTER_NODE_COMMAND]
  },
  "Jobs": [
    {
      "ExecutionId": "SAME_EXECUTION_ID",
      "ClusterName": "YOUR_FARGATE_CLUSTER",
      "TaskDefinition": "arn:aws:ecs:YOUR_REGION:YOUR_ACCOUNT_ID:task-definition/YOUR_TASK_NAME:1",
      "AwsRegion": "YOUR_REGION",
      "Subnets": [SUBNET_1, SUBNET_2],
      "SecurityGroups": [SECURITY_GROUP_TASKS_MUST_USE],
      "FamilyName": "YOUR_TASK_NAME",
      "WorkerTaskName": "YOUR_TASK_NAME",
      "WorkerCommand": [YOUR_WORKER_NODE_COMMAND]
    },
    {
      "ExecutionId": "SAME_EXECUTION_ID",
      "ClusterName": "YOUR_FARGATE_CLUSTER",
      "TaskDefinition": "arn:aws:ecs:YOUR_REGION:YOUR_ACCOUNT_ID:task-definition/YOUR_TASK_NAME:1",
      "AwsRegion": "YOUR_REGION",
      "Subnets": [SUBNET_1, SUBNET_2],
      "SecurityGroups": [SECURITY_GROUP_TASKS_MUST_USE],
      "FamilyName": "YOUR_TASK_NAME",
      "WorkerTaskName": "YOUR_TASK_NAME",
      "WorkerCommand": [YOUR_WORKER_NODE_COMMAND]
    }
  ]
}
```

Checkout the app example for a sample application using a custom Locust shape load.


### Sample application

See [here](./aws/example/README.md) for a sample load testing.
