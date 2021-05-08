import json
from interface import Fargate, DistributedLocust

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
            job.success(master_task)

    return None
        


# event = {
#     "JobDetails": {
#         "ExecutionId": "ddd",
#         "ClusterName": "ml-serving",
#         "FamilyName": "locust-load-test",
#         "MasterTaskName": "locust-load-test",
#         "Jobs": []
#     }
# }
# print(handler(event, {}))