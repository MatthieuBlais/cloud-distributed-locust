## Deploying infrastructure-as-code

### Cloudformation

All resources are defined and created using CloudFormation. There are two stacks to deploy:

1. fargate.yaml: To create a Fargate cluster and a staging S3 bucket. You can skip this step if you already have a cluster and a bucket you want to use.
2. stepfunction.yaml: To deploy the orchestration flow (Step Function) starting master node and worker nodes.

The additional stack is a sample Task definition that you can deploy to test the overall solution. It creates an ECR repository, a Fargate task definition and the IAM roles needed by the task.

### Deployment

1. (Optional) If you don't have a Fargate cluster yet, deploy the fargate.yaml template. Replace the placeholder by your own variables.

```
aws cloudformation deploy \
    --template-file fargate.yaml \
    --stack-name YOUR_STACK_NAME \
    --parameter-overrides clusterName=YOUR_CLUSTER_NAME stagingBucket=YOUR_BUCKET_NAME \
```

Make sure it is correctly deployed.

```
aws cloudformation describe-stack-resources \
    --stack-name distributed-locust-core
```

2. Package and upload your lambda code. Go to the lambdas folder and run the bash command.

```
cd ../lambdas
/bin/bash package.sh YOUR_BUCKET_NAME
```

3. Deploy the StepFunction. Replace the placeholders by your own variables

```
aws cloudformation deploy \
    --template-file stepfunction.yaml \
    --stack-name YOUR_STACK_NAME \
    --parameter-overrides stagingBucket=YOUR_BUCKET_NAME \
    --capabilities CAPABILITY_NAMED_IAM
```

4. Deploy the sample app. Modify the placeholder accordingly.

```
aws cloudformation deploy \
    --template-file sample-task.yaml \
    --stack-name YOUR_STACK_NAME \
    --parameter-overrides stagingBucket=YOUR_BUCKET_NAME subnet1Cidr=XX.XX.XX.XX/XX subnet2Cidr=XX.XX.XX.XX/XX vpcId=YOUR_VPC_ID \
    --capabilities CAPABILITY_NAMED_IAM
```

VpcID and subnets are required because we will start multiple tasks (one for the master node, the other ones for worker nodes) and they need to be able to communicate. We are not deploying everything as a single task as we need the flexibility to choose how many workers we want.
