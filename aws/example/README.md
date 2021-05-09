

aws ecr get-login-password --region YOUR_REGION | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.YOUR_REGION.amazonaws.com


docker build . -t  YOUR_ACCOUNT_ID.dkr.ecr.YOUR_REGION.amazonaws.com/distributed-locust/single-shape-load


aws s3 cp single-load-shape-test.json s3://YOUR_BUCKET/jobs/2021-05-09/000001.json




cd sample-api
chalice deploy
aws s3 cp sampledata.csv s3://YOUR_BUCKET/jobs/2021-05-09/sampledata.csv
