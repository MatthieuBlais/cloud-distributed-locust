import json

from interface import DistributedLocust
from interface import Fargate


def handler(event, context):
    """
    Check the status of the master Locust node
    """

    print("New event", json.dumps(event))

    job = DistributedLocust(event)
    fargate = Fargate(job.cluster)

    while fargate.has_tasks:
        tasks = fargate.fetch_tasks(job.task_family, fargate.next_token)

        if len(tasks) == 0:
            return job.failed()

        master_task = fargate.find_execution(tasks, job.task_name, job.execution_id)

        if master_task is None and not fargate.has_tasks:
            return job.failed()

        if master_task:
            return job.success(master_task)

    return None


event = {
    "JobDetails": {
        "ExecutionId": "ab0e1f2da1e511eb8992d9ddf1fe3780",
        "ClusterName": "mlops",
        "TaskDefinition": "arn:aws:ecs:ap-southeast-1:908177370303:task-definition/distributed-locust-single-shape-load:1",
        "AwsRegion": "ap-southeast-1",
        "Subnets": ["subnet-55476b32", "subnet-7581dc3c"],
        "SecurityGroups": ["sg-01044b90c2c0ad58e"],
        "FamilyName": "distributed-locust-single-shape-load",
        "MasterTaskName": "distributed-locust-single-shape-load",
        "MasterCommand": [
            "python3",
            "app/main.py",
            "--host",
            "https://d2yme6kw9k.execute-api.ap-southeast-1.amazonaws.com/api",
            "--method",
            "/hello",
            "--client-type",
            "master",
            "--expected-workers",
            "1",
            "--master-host",
            "0.0.0.0",
            "--shapes-bucket",
            "mlops-configs-20210509172522",
            "--shapes-key",
            "jobs/2021-05-09/000001.json",
            "--testdata-bucket",
            "mlops-configs-20210509172522",
            "--testdata-key",
            "jobs/2021-05-09/sampledata.csv",
            "--output-bucket",
            "mlops-configs-20210509172522",
            "--output-key",
            "jobs/2021-05-09/output.json",
        ],
    },
    "Jobs": [
        {
            "EndpointName": "loadtesting-dddd-0",
            "ExecutionId": "ab0e1f2da1e511eb8992d9ddf1fe3780",
            "ClusterName": "mlops",
            "TaskDefinition": "arn:aws:ecs:ap-southeast-1:908177370303:task-definition/distributed-locust-single-shape-load:1",
            "AwsRegion": "ap-southeast-1",
            "Subnets": ["subnet-55476b32", "subnet-7581dc3c"],
            "SecurityGroups": ["sg-01044b90c2c0ad58e"],
            "FamilyName": "distributed-locust-single-shape-load",
            "WorkerTaskName": "distributed-locust-single-shape-load",
            "WorkerCommand": [
                "python3",
                "app/main.py",
                "--host",
                "https://d2yme6kw9k.execute-api.ap-southeast-1.amazonaws.com/api",
                "--method",
                "/hello",
                "--client-type",
                "worker",
                "--shapes-bucket",
                "mlops-configs-20210509172522",
                "--shapes-key",
                "jobs/2021-05-09/000001.json",
                "--testdata-bucket",
                "mlops-configs-20210509172522",
                "--testdata-key",
                "jobs/2021-05-09/sampledata.csv",
            ],
        }
    ],
}
print(handler(event, {}))
