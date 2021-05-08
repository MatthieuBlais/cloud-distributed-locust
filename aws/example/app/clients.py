from interface import APIInterface, StagesShape
import time
import gevent
import datetime
from locust.env import Environment
from locust.stats import stats_printer, HISTORY_STATS_INTERVAL_SEC
import boto3
import os
import json
import sys

s3 = boto3.client('s3', region_name=os.environ["AWS_REGION"])
ecs = boto3.client('ecs', region_name=os.environ["AWS_REGION"])

class LoadClient():


    def __init__(self, host, shapes_location, output_location=None):

        self.stages_shape = StagesShape(shapes_location["Bucket"], shapes_location["Key"])
        self.env = Environment(user_classes=[APIInterface], shape_class=self.stages_shape)
        self.env.host = host
        self.output_location = output_location


    def stats_history(self, runner, percentiles=["50","95"]):
        """Save current stats info to history for charts of report."""
        while True:
            stats = runner.stats
            if not stats.total.use_response_times_cache:
                break
            if runner.state != "stopped":
                r = {
                    "time": datetime.datetime.now().strftime("%H:%M:%S"),
                    "current_rps": stats.total.current_rps or 0,
                    "current_fail_per_sec": stats.total.current_fail_per_sec or 0,
                    "user_count": runner.user_count or 0,
                }
                for percentile in percentiles:
                    pvalue = float(percentile) / (10**len(percentile))
                    r[f"response_time_percentile_{percentile}"] = stats.total.get_current_response_time_percentile(pvalue) or 0
                stats.history.append(r)
            gevent.sleep(HISTORY_STATS_INTERVAL_SEC)

    def wait_for_end(self, env, stages_shape, max_runtime):
        has_started = False
        start_time = time.time()
        while True:
            if self.env.runner.user_count > 0:
                has_started = True
            if has_started and self.env.runner.user_count == 0:
                self.env.runner.quit()
                return
            if max_runtime and time.time() - start_time > max_runtime:
                self.env.runner.quit()
                return
            gevent.sleep(HISTORY_STATS_INTERVAL_SEC)

    def check_master_status(self, env, max_runtime, fargate_task=None):
        start_time = time.time()
        while True:
            if max_runtime and time.time() - start_time > max_runtime:
                self.env.runner.quit()
                return
            if fargate_task:
                task = ecs.describe_tasks(
                    cluster=fargate_task.split("/")[1],
                    tasks=[
                        fargate_task
                    ]
                )
                if len(task['tasks']) != 1 or task['tasks'][0]['lastStatus'] == "STOPPED":
                    self.env.runner.quit()
                    return
            gevent.sleep(60)

    def save_results(self, percentiles):
        results = {
            "time": datetime.datetime.now().strftime("%H:%M:%S"),
            "min_response_time": self.env.stats.total.min_response_time,
            "max_response_time": self.env.stats.total.max_response_time,
            "num_requests": self.env.stats.total.num_requests,
            "history": self.env.stats.history
        }
        if len(self.env.stats.history) > 0:
            for percentile in percentiles:
                results[f"response_time_percentile_{percentile}"] = sum([x[f"response_time_percentile_{percentile}"] for x in self.env.stats.history]) / len(self.env.stats.history)
        if self.output_location:
            self.upload_report(self.output_location['Bucket'], self.output_location['Key'], results)
        print(results)


    def upload_report(self, bucket, key, results):
        """Save output to S3"""
        existing = []
        try:
            obj = s3.get_object(Bucket=bucket, Key=key)
            existing = json.loads(obj['Body'].read())
        except Exception:
            existing = []
        existing.append(results)
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(existing)
        )



class MasterLoadClient(LoadClient):
    """Master client"""

    def __init__(self, expected_workers, master_host="127.0.0.1", master_port=5557, percentiles="50,95", max_runtime=None, *args, **kwargs):
        """Initialize master locust node"""
        super(MasterLoadClient, self).__init__(*args, **kwargs)
        self.env.create_master_runner(master_host, master_port)
        self.stages_shape.runner = self.env.runner
        self.percentiles = percentiles.split(",")
        self.expected_workers = int(expected_workers)
        self.max_runtime = max_runtime

    def start(self):
        """Wait for all worker nodes to connect and start the load testing"""
        while len(self.env.runner.clients.ready) < self.expected_workers:
            time.sleep(1)

        gevent.spawn(stats_printer(self.env.stats))
        gevent.spawn(self.stats_history, self.env.runner, self.percentiles)
        self.env.runner.start_shape()
        gevent.spawn_later(20, self.wait_for_end(self.env, self.stages_shape, self.max_runtime))
        self.save_results(self.percentiles)


class WorkerLoadClient(LoadClient):
    """Simply trigger worker connecting to a master locust"""

    def __init__(self, master_host="127.0.0.1", master_port=5557, master_fargate_task=None, max_runtime=None, *args, **kwargs):
        """Initialize worker node by connecting to the master node and setting a max runtime to automatically stop. Useful when the master node stops working."""
        super(WorkerLoadClient, self).__init__(*args, **kwargs)
        self.env.create_worker_runner(master_host, master_port)
        self.master_fargate_task = master_fargate_task
        self.max_runtime = max_runtime

    def start(self):
        """Start a worker node if a master node exists and wait for the task to complete"""
        if self.master_fargate_task:
            gevent.spawn_later(20, self.check_master_status(self.env, self.max_runtime, self.master_fargate_task))
        self.env.runner.greenlet.join()


class LocalLoadClient(LoadClient):
    """To run shape load locally"""

    def __init__(self, percentiles="50,95", max_runtime=None, *args, **kwargs):
        """Initialize local locust client"""
        super(LocalLoadClient, self).__init__(*args, **kwargs)
        self.env.create_local_runner()
        self.stages_shape.runner = self.env.runner
        self.percentiles = percentiles.split(",")
        self.max_runtime = max_runtime
        
    def start(self):
        """Start the client and wait for it to complete"""
        gevent.spawn(stats_printer(self.env.stats))
        gevent.spawn(self.stats_history, self.env.runner, self.percentiles)
        self.env.runner.start_shape()
        gevent.spawn_later(20, self.wait_for_end(self.env, self.stages_shape, self.max_runtime))
        self.save_results(self.percentiles)
