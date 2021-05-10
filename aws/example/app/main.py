import argparse
import datetime
import json
import os
import sys

import boto3
from client import DistributedClient
from locust.log import setup_logging
from shape import APIInterface
from shape import StagesShape

setup_logging("INFO", None)


class LoadTesting(DistributedClient):
    def __init__(self, shapes_location, output_location, region, *args, **kwargs):
        stages_shape = StagesShape(
            shapes_location["Bucket"], shapes_location["Key"], region
        )
        super(LoadTesting, self).__init__(stages_shape=stages_shape, *args, **kwargs)
        self.output_location = output_location
        self.region = region

    def start(self):
        if self.node_type == "master":
            self.start_master()
        elif self.node_type == "worker":
            self.start_worker()
        else:
            self.start_local()

    def save_results(self, percentiles):
        results = {
            "time": datetime.datetime.now().strftime("%H:%M:%S"),
            "min_response_time": self.env.stats.total.min_response_time,
            "max_response_time": self.env.stats.total.max_response_time,
            "num_requests": self.env.stats.total.num_requests,
            "history": self.env.stats.history,
        }
        if len(self.env.stats.history) > 0:
            for percentile in percentiles:
                results[f"response_time_percentile_{percentile}"] = sum(
                    [
                        x[f"response_time_percentile_{percentile}"]
                        for x in self.env.stats.history
                    ]
                ) / len(self.env.stats.history)
        if self.output_location:
            self.upload_report(
                self.output_location["Bucket"], self.output_location["Key"], results
            )

    def upload_report(self, bucket, key, results):
        """Save output to S3"""
        s3 = boto3.client("s3", region_name=os.environ["AWS_REGION"])
        report = self._download_previous_report(s3, bucket, key)
        report.append(results)
        s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(report))

    def _download_previous_report(self, s3, bucket, key):
        """Download previous report if exists"""
        try:
            obj = s3.get_object(Bucket=bucket, Key=key)
            return json.loads(obj["Body"].read())
        except Exception:
            return []


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", "-H")
    parser.add_argument("--method", default="/")
    parser.add_argument("--shapes-bucket")
    parser.add_argument("--shapes-key")
    parser.add_argument("--testdata-bucket")
    parser.add_argument("--testdata-key")
    parser.add_argument("--client-type", default="local")
    parser.add_argument("--master-host", default="127.0.0.1")
    parser.add_argument("--master-port", default=5557)
    parser.add_argument("--expected-workers", default=1)
    parser.add_argument("--output-bucket", default=None)
    parser.add_argument("--output-key", default=None)
    parser.add_argument("--percentiles", default="50,95")
    parser.add_argument("--max-runtime", default=None)
    parser.add_argument("--fargate-task", default=None)
    parser.add_argument("--region", default="ap-southeast-1")
    parser.add_argument("--content-type", default="application/json")
    args = parser.parse_args()
    set_env(args)
    return args


def set_env(args):
    os.environ["AWS_REGION"] = args.region
    os.environ["METHOD_PATH"] = args.method
    os.environ["CONTENT_TYPE"] = args.content_type
    os.environ["TEST_DATASET_BUCKET"] = args.testdata_bucket
    os.environ["TEST_DATASET_KEY"] = args.testdata_key


if __name__ == "__main__":
    print(sys.argv)
    args = parse_args()
    client = LoadTesting(
        shapes_location={"Bucket": args.shapes_bucket, "Key": args.shapes_key},
        output_location={"Bucket": args.output_bucket, "Key": args.output_key}
        if args.output_bucket is not None or args.output_key is not None
        else None,
        node_type=args.client_type,
        host=args.host,
        user_classes=[APIInterface],
        expected_workers=args.expected_workers,
        percentiles=args.percentiles,
        max_runtime=args.max_runtime,
        master_host=args.master_host,
        master_port=args.master_port,
        master_fargate_task=args.fargate_task,
        region=args.region,
    )
    client.start()
