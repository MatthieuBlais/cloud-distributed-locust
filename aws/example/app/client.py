import datetime
import logging

import boto3
import gevent
import sys
import time

from locust.env import Environment
from locust.stats import HISTORY_STATS_INTERVAL_SEC
from locust.stats import stats_printer


class DistributedClient:
    def __init__(
        self,
        node_type,
        host,
        stages_shape,
        user_classes=[],
        expected_workers=1,
        master_host="127.0.0.1",
        master_port=5557,
        percentiles="50,95",
        master_fargate_task=None,
        max_runtime=None,
        region="ap-southeast-1",
    ):
        node_type = node_type.lower()
        if node_type not in ["worker", "master", "local"]:
            logging.error("Node type must be one of worker, master, local")
            sys.exit(1)

        self.stages_shape = stages_shape
        self.env = Environment(user_classes=user_classes, shape_class=self.stages_shape)
        self.env.host = host
        self.max_runtime = max_runtime
        self.node_type = node_type
        self.ecs = boto3.client("ecs", region_name=region)

        if node_type == "worker":
            self.env.create_worker_runner(master_host, master_port)
            self.master_fargate_task = master_fargate_task
        else:
            if node_type == "master":
                self.env.create_master_runner(master_host, master_port)
                self.expected_workers = int(expected_workers)
            if node_type == "local":
                self.env.create_local_runner()

            self.stages_shape.runner = self.env.runner
            self.percentiles = percentiles.split(",")

    def start_master(self):
        """Wait for all worker nodes to connect and start the load testing"""
        while len(self.env.runner.clients.ready) < self.expected_workers:
            time.sleep(1)
        gevent.spawn(stats_printer(self.env.stats))
        gevent.spawn(self.stats_history, self.env.runner, self.percentiles)
        self.env.runner.start_shape()
        gevent.spawn_later(
            20, self.wait_for_end(self.env, self.stages_shape, self.max_runtime)
        )
        self.save_results(self.percentiles)

    def start_worker(self):
        """Start a worker node if a master node exists and wait for the task to complete"""
        if self.master_fargate_task:
            gevent.spawn_later(
                20,
                self._master_status(
                    self.env, self.max_runtime, self.master_fargate_task
                ),
            )
        self.env.runner.greenlet.join()

    def start_local(self):
        """Start the client and wait for it to complete"""
        gevent.spawn(stats_printer(self.env.stats))
        gevent.spawn(self.stats_history, self.env.runner, self.percentiles)
        self.env.runner.start_shape()
        gevent.spawn_later(
            20, self.wait_for_end(self.env, self.stages_shape, self.max_runtime)
        )
        self.save_results(self.percentiles)

    def stats_history(self, runner, percentiles=["50", "95"]):
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
                    pvalue = float(percentile) / (10 ** len(percentile))
                    r[f"response_time_percentile_{percentile}"] = (
                        stats.total.get_current_response_time_percentile(pvalue) or 0
                    )
                stats.history.append(r)
            gevent.sleep(HISTORY_STATS_INTERVAL_SEC)

    def wait_for_end(self, env, stages_shape, max_runtime):
        """Stop master node when the number of users goes back to 0"""
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

    def _master_status(self, env, max_runtime, fargate_task=None):
        """Worker node need to exit if the overall task takes too much time or if the master node dies"""
        start_time = time.time()
        while True:
            if max_runtime and time.time() - start_time > max_runtime:
                self.env.runner.quit()
                return
            if fargate_task:
                task = self.ecs.describe_tasks(
                    cluster=fargate_task.split("/")[1], tasks=[fargate_task]
                )
                if (
                    len(task["tasks"]) != 1
                    or task["tasks"][0]["lastStatus"] == "STOPPED"
                ):
                    self.env.runner.quit()
                    return
            gevent.sleep(60)

    def save_results(self, percentiles):
        """To implement if need to save results somewhere"""
        pass
