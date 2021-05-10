


zip -r9 ../distributedlocust.zip . -x \*.git\* -x \*.pyc\* -x \*__pycache__\*

cd ..

aws s3 mv distributedlocust.zip "s3://mlops-configs-20210509172522/_lambdas/distributedlocust.zip"
