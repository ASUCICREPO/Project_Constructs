This CDK uses Application Load Balancer, ECS and ECR

Pre-requisites:

1. Python3 is installed on your system
2. virtualenv library is installed (run the command `pip install virtualenv`)
3. Docker is installed and running on your machine
4. AWS CLI installed and setup (make sure you have generated the secret credentials from AWS IAM and set the coorect region in aws cli)

To deploy this construct follow the steps below:

1. Create a new folder and then create a virtual env using the command
    `virtualenv venv`
2. Activate the virtual env from command line
3. From the root directory of this project run the following command to install all cdk python libraries:
    `pip install -r requirements.txt`
4. Run the following command to make sure our environment is bootstrapped:
    `cdk bootstrap`
5. Run the following command to authenticate in Public ECR then only it will be able to download python public image for ECR:
    `aws ecr-public get-login-password --region <region-name> | docker login --username AWS --password-stdin public.ecr.aws`
Replace the `<region-name>` with the actual region name
6. Run the following command to make sure the CDK code is synthesized:
    `cdk synth`
7. Run the following command that will deploy the application:
    `cdk deploy`
8. After the successful deployment we can use test the CDK deployment

To test the application follow the steps below:

1. Go to the Application load balancer in AWS console and find the load balancer thay was created as a part of this CDK deployment. Click on that load balancer
2. Copy the `DNS Name` of the load balancer
3. Paste the `DNS Name` of the load balancer in browser and click enter
4. You will get the following message in the browser:
`{"message":"Hello from Dockerized Flask App!"}`
This means the deployment was successful and everything is working correctly

![My Image](Architecture_Diagram.png)

In the above architecture diagram auser is calling the load balancer from the brower. The load balancer redirects the reques to the ECS service and this ECS service is runnign a task.

The task is a dockerized container which is being feteched from ECR.

You can add your application code in the `docker/app.py` file in the root directory of this CDK project and you can also modify the `Dockerfile`. You can modify everything in this docker folder and run any dockerized application. When you do `cdk deploy` it is automatically going to create dockerized container and upload that to ECR whick will get run in form of ECS service.
