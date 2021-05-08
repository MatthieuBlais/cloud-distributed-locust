from locust.log import setup_logging
import argparse
import os
from client import MasterLoadClient, WorkerLoadClient, LocalLoadClient

setup_logging("INFO", None)

def load_testing(client_type, host, shapes_location, output_location=None, percentiles="50,95", max_runtime=None, master_host="127.0.0.1", master_port=5557, expected_workers=1, master_fargate_task=None):

    client = LocalLoadClient(percentiles=percentiles, max_runtime=max_runtime, host=host, shapes_location=shapes_location, output_location=output_location)
    if client_type == "master":
        client = MasterLoadClient(expected_workers=expected_workers, percentiles=percentiles, max_runtime=max_runtime, master_host=master_host, master_port=master_port, host=host, shapes_location=shapes_location, output_location=output_location)
    elif client_type == "worker":
        client = WorkerLoadClient(master_host=master_host, master_port=master_port, host=host, shapes_location=shapes_location, master_fargate_task=master_fargate_task)
    
    client.start()

    
def parse_args():
    os.environ["AWS_REGION"] = os.environ.get("AWS_REGION", "ap-southeast-1")
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", "-H")
    parser.add_argument("--shapes-bucket")
    parser.add_argument("--shapes-key")
    parser.add_argument("--client-type", default="local")
    parser.add_argument("--master-host", default="127.0.0.1")
    parser.add_argument("--master-port", default=5557)
    parser.add_argument("--expected-workers", default=1)
    parser.add_argument("--output-bucket", default=None)
    parser.add_argument("--output-key", default=None)
    parser.add_argument("--percentiles", default="50,95")
    parser.add_argument("--max-runtime", default=None)
    parser.add_argument("--fargate-task", default=None)
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parse_args()

    print(f"Configuration: host={args.host}, output=s3://{args.output_bucket}/{args.output_key}, percentiles={args.percentiles}")
    load_testing(
        args.client_type,
        args.host,
        { "Bucket": args.shapes_bucket, "Key": args.shapes_key },
        { "Bucket": args.output_bucket, "Key": args.output_key },
        args.percentiles,
        args.max_runtime,
        args.master_host,
        args.master_port,
        args.expected_workers,
        args.fargate_task
    )