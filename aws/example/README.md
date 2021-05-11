### Sample Shape Load Testing


### 1. Deploy an API endpoint

For this sample, we will use a dummy API endpoint, created with [AWS Chalice](https://github.com/aws/chalice). To install Chalice use:

```
pip install chalice
```

Run the API locally with:

```
chalice local
```

There is one POST endpoint /hello accepting a JSON body { "hello": "yourname" }. Make sure the API works locally, then deploy it using:

```
chalice deploy
```

Take note of your API Gateway endpoint


### 2. Prepare data

Our Workers will need to provide the JSON body in their requests. Upload the sample data to your Staging bucket.

```
aws s3 cp sample-api/sampledata.csv s3://YOUR_BUCKET/jobs/2021-05-09/sampledata.csv
```

Let's define our [load shape](./single-load-shape-test.json):

```
[
    {"users": 10, "duration": 15, "spawn_rate": 100},
    {"users": 20, "duration": 30, "spawn_rate": 100},
    {"users": 30, "duration": 45, "spawn_rate": 100},
    {"users": 10, "duration": 60, "spawn_rate": 100},
    {"users": 0, "duration": 75, "spawn_rate": 100}
]
```

We start with 10 users for 15seconds, then we increase to 20 users for 15 more seconds. Make sure to have users:0 as the last step to indicate the load testing is over. The spawn rate is the speed at which you spawn users (same definition as Locust). A more advanced example is given [here](single-load-shape.json)

Upload the load shape to your staging bucket:

```
aws s3 cp single-load-shape-test.json s3://YOUR_BUCKET/jobs/2021-05-09/000001.json
```


### 3. Test Locust locally

Try to run Locust on your local environment first.

```
python app/main.py \
    --host https://YOUR_API_ID.execute-api.YOUR_REGION.amazonaws.com/api \
    --method /hello \
    --shapes-bucket YOUR_BUCKET \
    --shapes-key jobs/2021-05-09/000001.json \
    --testdata-bucket YOUR_BUCKET \
    --testdata-key jobs/2021-05-09/sampledata.csv
```

### 4. Prepare your container

Build the Docker container for this sample app. Tag it to be pushed to your ECR repository

```
docker build . -t  YOUR_ACCOUNT_ID.dkr.ecr.YOUR_REGION.amazonaws.com/YOUR_ECR_REPO
```

You can test locally that everything looks fine. Replace the variables by your own variables.

```
docker run \
     -p 5557:5557 \
     -e AWS_REGION=YOUR_REGION \
     -e AWS_ACCESS_KEY_ID=YOUR_AWS_KEY \
     -e AWS_SECRET_ACCESS_KEY=YOUR_AWS_SECRET \
     -it YOUR_ACCOUNT_ID.dkr.ecr.YOUR_REGION.amazonaws.com/YOUR_ECR_REPO python app/main.py \
     --host https://YOUR_API_ID.execute-api.YOUR_REGION.amazonaws.com/api/ \
     --method /hello \
     --client-type master \
     --expected-workers 1 \
     --master-host 0.0.0.0 \
     --testdata-bucket YOUR_BUCKET \
     --testdata-key jobs/2021-05-09/sampledata.csv \
     --shapes-bucket YOUR_BUCKET \
     --shapes-key jobs/2021-05-09/000001.json

docker run \
     -p 5557:5557 \
     -e AWS_REGION=YOUR_REGION \
     -e AWS_ACCESS_KEY_ID=YOUR_AWS_KEY \
     -e AWS_SECRET_ACCESS_KEY=YOUR_AWS_SECRET \
     -it YOUR_ACCOUNT_ID.dkr.ecr.YOUR_REGION.amazonaws.com/YOUR_ECR_REPO python app/main.py \
     --host https://YOUR_API_ID.execute-api.YOUR_REGION.amazonaws.com/api/ \
     --method /hello \
     --client-type worker \
     --testdata-bucket YOUR_BUCKET \
     --testdata-key jobs/2021-05-09/sampledata.csv \
     --shapes-bucket YOUR_BUCKET \
     --shapes-key jobs/2021-05-09/000001.json
```

We specify we expect only 1 worker. The app will wait for 1 worker to connect before starting the load test. You may run these two commands in different terminals if you want to check the logs.

Once good, push to ECR

```
aws ecr get-login-password --region YOUR_REGION | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.YOUR_REGION.amazonaws.com

docker push YOUR_ACCOUNT_ID.dkr.ecr.YOUR_REGION.amazonaws.com/distributed-locust/single-shape-load
```


### 6. Trigger


I've used distributed-locust-single-shape-load as task name. Replace remaining variables.

```
{
  "JobDetails": {
    "ExecutionId": "ab0e1f2da1e511eb8992d9ddf1fe3780",
    "ClusterName": "YOUR_FARGATE_CLUSTER",
    "TaskDefinition": "arn:aws:ecs:YOUR_REGION:YOUR_ACCOUNT_ID:task-definition/distributed-locust-single-shape-load:1",
    "AwsRegion": "YOUR_REGION",
    "Subnets": [SUBNET_1, SUBNET_2],
    "SecurityGroups": [SECURITY_GROUP_TASKS_MUST_USE],
    "FamilyName": "distributed-locust-single-shape-load",
    "MasterTaskName": "distributed-locust-single-shape-load",
    "MasterCommand": [
      "python3",
      "app/main.py",
      "--host",
      "https://YOUR_API_ID.execute-api.YOUR_REGION.amazonaws.com/api",
      "--method",
      "/hello",
      "--client-type",
      "master",
      "--expected-workers",
      "1",
      "--master-host",
      "0.0.0.0",
      "--shapes-bucket",
      "YOUR_BUCKET",
      "--shapes-key",
      "jobs/2021-05-09/000001.json",
      "--testdata-bucket",
      "YOUR_BUCKET",
      "--testdata-key",
      "jobs/2021-05-09/sampledata.csv",
      "--output-bucket",
      "YOUR_BUCKET",
      "--output-key",
      "jobs/2021-05-09/output.json"
    ]
  },
  "Jobs": [
    {
      "ExecutionId": "ab0e1f2da1e511eb8992d9ddf1fe3780",
      "ClusterName": "YOUR_FARGATE_CLUSTER",
      "TaskDefinition": "arn:aws:ecs:YOUR_REGION:YOUR_ACCOUNT_ID:task-definition/distributed-locust-single-shape-load:1",
      "AwsRegion": "YOUR_REGION",
      "Subnets": [SUBNET_1, SUBNET_2],
      "SecurityGroups": [SECURITY_GROUP_TASKS_MUST_USE],
      "FamilyName": "distributed-locust-single-shape-load",
      "WorkerTaskName": "distributed-locust-single-shape-load",
      "WorkerCommand": [
        "python3",
        "app/main.py",
        "--host",
        "https://YOUR_API_ID.execute-api.YOUR_REGION.amazonaws.com/api",
        "--method",
        "/hello",
        "--client-type",
        "worker",
        "--shapes-bucket",
        "YOUR_BUCKET",
        "--shapes-key",
        "jobs/2021-05-09/000001.json",
        "--testdata-bucket",
        "YOUR_BUCKET",
        "--testdata-key",
        "jobs/2021-05-09/sampledata.csv"
      ]
    }
  ]
}
```

The output of the performance testing will be in s3://YOUR_BUCKET/jobs/2021-05-09/output.json.
