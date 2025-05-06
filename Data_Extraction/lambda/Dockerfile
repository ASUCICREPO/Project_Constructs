# Use the official AWS Lambda Python 3.10 runtime base image
FROM public.ecr.aws/lambda/python:3.10

COPY lambda_function.py /asset/
COPY requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt -t /asset