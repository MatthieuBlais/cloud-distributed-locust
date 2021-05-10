


aws s3 cp single-load-shape-test.json s3://YOUR_BUCKET/jobs/2021-05-09/000001.json


cd sample-api
chalice deploy
aws s3 cp sampledata.csv s3://YOUR_BUCKET/jobs/2021-05-09/sampledata.csv


python app/main.py \
    --host https://YOUR_API_ID.execute-api.YOUR_REGION.amazonaws.com/api \
    --method /hello \
    --shapes-bucket YOUR_BUCKET \
    --shapes-key jobs/2021-05-09/000001.json \
    --testdata-bucket YOUR_BUCKET \
    --testdata-key jobs/2021-05-09/sampledata.csv



aws ecr get-login-password --region YOUR_REGION | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.YOUR_REGION.amazonaws.com


docker build . -t  YOUR_ACCOUNT_ID.dkr.ecr.YOUR_REGION.amazonaws.com/distributed-locust/single-shape-load


docker run \
     -p 5557:5557 \
     -e AWS_REGION=YOUR_REGION \
     -e AWS_ACCESS_KEY_ID=YOUR_AWS_KEY \
     -e AWS_SECRET_ACCESS_KEY=YOUR_AWS_SECRET \
     -it YOUR_ACCOUNT_ID.dkr.ecr.YOUR_REGION.amazonaws.com/distributed-locust/single-shape-load python app/main.py \
     --host https://YOUR_API_ID.execute-api.YOUR_REGION.amazonaws.com/api/ \
     --method /hello \
     --client-type master \
     --expected-workers 1 \
     --master-host 0.0.0.0 \
     --testdata-bucket YOUR_BUCKET \
     --testdata-key jobs/2021-05-09/sampledata.csv \
     --shapes-bucket YOUR_BUCKET \
     --shapes-key jobs/2021-05-09/000001.json


docker push YOUR_ACCOUNT_ID.dkr.ecr.YOUR_REGION.amazonaws.com/distributed-locust/single-shape-load
