import csv
import json
import os

import boto3
from locust import between
from locust import LoadTestShape
from locust import task
from locust.contrib.fasthttp import FastHttpUser


class StagesShape(LoadTestShape):
    """
    Shapes must look like this, uploaded to a bucket
    stages = [
        {"duration": 30, "users": 100, "spawn_rate": 100},
        {"duration": 60, "users": 150, "spawn_rate": 100},
        {"duration": 90, "users": 200, "spawn_rate": 100},
        {"duration": 120, "users": 130, "spawn_rate": 100},
        {"duration": 150, "users": 310, "spawn_rate": 100},
        {"duration": 180, "users": 100, "spawn_rate": 100},
        {"duration": 210, "users": 0, "spawn_rate": 100}
    ]
    """

    time_limit = 600
    spawn_rate = 20
    stop_at_end = True
    stages = []

    def __init__(self, stages_bucket, stages_key, mode="users", *args, **kwargs):
        self.s3 = boto3.client("s3", region_name=os.environ["AWS_REGION"])
        self.stages = self.download_stages(stages_bucket, stages_key)
        self.step = 0
        self.time_active = False
        self.runner = None
        self.mode = mode
        super(StagesShape, self).__init__(*args, **kwargs)

    def tick(self):
        """Called at every tick to control user spawning"""
        if self.mode == "time":
            return self.tick_time()
        else:
            return self.tick_users()

    def tick_users(self):
        """Spawn users: trigger duration only when all users are ready"""
        if self.step >= len(self.stages) or self.runner is None:
            return None

        target = self.stages[self.step]
        users = self.runner.user_count

        if target["users"] == users:
            if not self.time_active:
                self.reset_time()
                self.time_active = True
            run_time = self.get_run_time()
            if run_time > target["duration"]:
                self.step += 1
                self.time_active = False

        return (target["users"], target["spawn_rate"])

    def tick_time(self):
        """Spawn users: trigger duration based on time only (event if not all users ready)"""
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                tick_data = (stage["users"], stage["spawn_rate"])
                return tick_data
        return None

    def download_stages(self, bucket, key):
        """Download stages from S3"""
        obj = self.s3.get_object(Bucket=bucket, Key=key)
        return json.loads(obj["Body"].read())


class APIInterface(FastHttpUser):
    """
    Client calling the API. Download test data and submit post requests
    """

    wait_time = between(1, 2)

    def __init__(self, *args, **kwargs):
        super(APIInterface, self).__init__(*args, **kwargs)
        self.s3 = boto3.client("s3", region_name=os.environ["AWS_REGION"])
        self.method_path = os.environ["METHOD_PATH"]
        self.headers = {
            "Content-Type": os.environ.get("CONTENT_TYPE", "application/json"),
            "Accept": "application/json",
        }

    @task
    def index(self):
        self.client.post(
            self.method_path, data=self.testdata[self.data_idx], headers=self.headers
        )
        self.data_idx += 1
        if self.data_idx == self.total_data:
            self.data_idx = 0

    def on_start(self):
        """When locust starts, download test dataset from bucket"""
        dataset = self.download_test_set()
        self.testdata = []
        self.testexpected = []
        reader = csv.reader(dataset, delimiter=",")
        next(reader)
        for row in reader:
            self.testdata.append(row[0])
        self.total_data = len(self.testdata)
        self.data_idx = 0

    def download_test_set(self):
        """Download test set from S3"""
        obj = self.s3.get_object(
            Bucket=os.environ["TEST_DATASET_BUCKET"], Key=os.environ["TEST_DATASET_KEY"]
        )
        return obj["Body"].read().decode().split()
