import boto3
import os

class Fargate():
    """Interface to interact with Fargate tasks"""

    def __init__(self, cluster, region_name=os.environ.get("AWS_REGION", "ap-southeast-1")):
        """Initialize ECS client"""
        self.cluster = cluster
        self.client = boto3.client('ecs', region_name=region_name)
        self.has_tasks = True
        self.next_token = None


    def fetch_tasks(self, family, next_token=None):
        """
        Fetch running tasks in Fargate cluster and return the list + next page token
            cluster: Name of the Fargate cluster
            family: Task family
        """
        params = {
            'cluster': self.cluster,
            'family': family,
        }
        if next_token:
            params['nextToken'] = next_token
        response = self.client.list_tasks(**params)
        self.next_token = response.get("nextToken")
        self.has_tasks = self.next_token is not None
        return response['taskArns']

    def find_execution(self, tasks, task_name, execution_id):
        """Describe all running tasks, and try to find the execution based on task name and execution id"""
        descriptions = self.client.describe_tasks(
            cluster=self.cluster,
            tasks=tasks
        )
        return self._filter(descriptions['tasks'], task_name, execution_id)

    def _filter(self, tasks, task_name, execution_id):
        """Filter the tasks based on name and execution id"""
        for task in tasks:
            if self._has_name(task, task_name) and self._is_execution(execution_id):
                return task
        return None

    def _has_name(self, task, name):
        """Check if container name is the same as the one we're looking for"""
        return task['overrides']['containerOverrides'][0]['name'] == name

    def _is_execution(self, execution_id):
        """Check if the execution id is the same as the one we're looking for"""
        for env_var in task['overrides']['containerOverrides'][0]['environment']:
            if env_var['name'] == 'EXECUTION_ID' and env_var['value'] == execution_id:
                return True
        return False
        

class DistributedLocust():
    """Interface for distributed locust"""

    def __init__(self, event):
        """Parse job event"""
        self.event = event
        details = event["JobDetails"]
        self.cluster = details["ClusterName"]
        self.task_family = details["FamilyName"]
        self.task_name = details["MasterTaskName"]
        self.execution_id = details["ExecutionId"]
        self.jobs = self.event['Jobs']

    def failed(self):
        """Task is not running, must have crashed"""
        self.event['MasterStatus'] = 'STOPPED'
        return self.event

    def success(self, task):
        """Task is running and ready to access workers"""
        self.event["MasterStatus"] = task['lastStatus']
        self.event['MasterTaskArn'] = task['taskArn']
        self.event['MasterPrivateIp'] = self._extract_private_ip(task)
        self.event['Jobs'] = self._configure_workers(self.jobs, self.event['MasterPrivateIp'], self.event['MasterTaskArn'])
        return self.event

    def _extract_private_ip(self, task):
        """Extract IP address for workers to know how to connect to the master node"""
        for x in task['attachments']:
            if x['type'] == 'ElasticNetworkInterface':
                for det in x['details']:
                    if det['name'] == 'privateIPv4Address':
                        return det['value']
        return None

    def _configure_workers(self, workers, ip_address, task_arn):
        """Add the master node details to the worker nodes. They will be used to established the connection"""
        params = [
            "--master-host",
            ip_address,
            "--fargate-task",
            task_arn
        ]
        for i in range(len(workers)):
            workers[i]["WorkerCommand"] += params
        return workers