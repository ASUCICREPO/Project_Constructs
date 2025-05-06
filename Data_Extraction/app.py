from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_s3_notifications as s3n,
    App,
    Duration
)
from constructs import Construct



class DocumentProcessingStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create an S3 bucket to store documents
        bucket = s3.Bucket(
            self,
            "DocumentsBucket_BDADemo",
            removal_policy=RemovalPolicy.DESTROY
        )
        
        # Create an S3 bucket to store documents
        output_bucket = s3.Bucket(
            self,
            "DocumentsBucket_BDADemo_Output",
            removal_policy=RemovalPolicy.DESTROY
        )

        # Create a DynamoDB table to store structured data
        table = dynamodb.Table(
            self,
            "ProcessedDocumentsTable",
            partition_key=dynamodb.Attribute(name="document_id", type=dynamodb.AttributeType.STRING),
            removal_policy=RemovalPolicy.DESTROY
        )

        # Create IAM Role for the Lambda function
        lambda_role = iam.Role(
            self,
            "LambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonDynamoDBFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AdministratorAccess")
            ]
        )

        # Create the Lambda function
        lambda_function = _lambda.Function(
            self,
            "TextractProcessingFunction",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="lambda_function.handler",
            code=_lambda.Code.from_docker_build(
                "lambda",
        ), # Path to the folder with your Lambda code
            environment={
                "OUTPUT_BUCKET": output_bucket.bucket_name,
                "DYNAMODB_TABLE": table.table_name
            },
            role=lambda_role,
            timeout=Duration.seconds(300),
        )


        # Add S3 trigger to Lambda
        bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(lambda_function)
        )

        # Grant permissions to Lambda for S3 and DynamoDB
        bucket.grant_read_write(lambda_function)
        table.grant_write_data(lambda_function)

app = App()
DocumentProcessingStack(app, "DocumentProcessingStack")
app.synth()