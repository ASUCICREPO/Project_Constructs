import json
import boto3
import os
import time
from urllib.parse import urlparse
import uuid
# Initialize Bedrock clients
bedrock_client = boto3.client('bedrock-data-automation', region_name='us-west-2')
bedrock_runtime_client = boto3.client('bedrock-data-automation-runtime', region_name='us-west-2')

# Initialize S3 client
s3_client = boto3.client('s3')

# Initialize DynamoDB client
dynamodb_client = boto3.resource('dynamodb')

# DynamoDB table name (replace with your table name)
DYNAMODB_TABLE_NAME = os.getenv('DYNAMODB_TABLE', 'YourDynamoDBTableName')
OUTPUT_BUCKET = os.getenv('OUTPUT_BUCKET', 'YourOutputBucketName')

def handler(event, context):
    # Get S3 bucket and object key from event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']

    print(f"Event: {json.dumps(event)}")

    try:
        # Step 1: Create Bedrock data automation project
        
        # Step 2: Invoke data automation job asynchronously
        input_s3_uri = f's3://{bucket_name}/{object_key}'
        output_s3_uri = f's3://{OUTPUT_BUCKET}/output_{object_key}'

        schema = '''
        {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "description": "default",
            "documentClass": "default",
            "type": "object",
            "definitions": {},
            "properties": {
                "ssn number": {
                    "type": "string",
                    "inferenceType": "extractive",
                    "description": "extract ssn number"
                },
                "wages and other componsation": {
                    "type": "string",
                    "inferenceType": "extractive",
                    "description": "extract wages and other compensation details"
                }
            }
        }
        '''

        response_blueprint = bedrock_client.create_blueprint(
            blueprintName=f'{uuid.uuid4()}',
            type='DOCUMENT',
            blueprintStage='DEVELOPMENT',
            schema=schema
        )

        response_runtime = bedrock_runtime_client.invoke_data_automation_async(
            inputConfiguration={'s3Uri': input_s3_uri},
            outputConfiguration={'s3Uri': output_s3_uri},
            blueprints=[
                {
                    'blueprintArn': response_blueprint["blueprint"]["blueprintArn"],
                    'stage': 'DEVELOPMENT'
                },
            ]
        )

        # Step 3: Parse job metadata JSON
        job_metadata_key = f'{output_s3_uri}/{response_runtime["invocationArn"].split("/")[-1]}/job_metadata.json'
        
        print("Job key metadata: ", job_metadata_key)
        time.sleep(20)
        parsed_uri = urlparse(job_metadata_key)
        bucket_name = parsed_uri.netloc  # Extract the bucket name
        object_key = parsed_uri.path.lstrip('/') 
        job_metadata_object = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        job_metadata = json.loads(job_metadata_object['Body'].read().decode('utf-8'))

        # Step 4: Download and parse custom output JSON
        custom_output_path = job_metadata["output_metadata"][0]["segment_metadata"][0]["custom_output_path"]
        custom_output_object = s3_client.get_object(Bucket=bucket_name, Key=custom_output_path.replace(f's3://{bucket_name}/', ''))
        custom_output = json.loads(custom_output_object['Body'].read().decode('utf-8'))

        # Step 5: Extract inference results
        inference_result = custom_output.get("inference_result", {})
        ssn_number = inference_result.get("ssn number", "")
        wages_and_compensation = inference_result.get("wages and other componsation", "")

        # Step 6: Store results in DynamoDB
        dynamodb_table = dynamodb_client.Table(DYNAMODB_TABLE_NAME)
        dynamodb_table.put_item(
            Item={
                'document_id': str(uuid.uuid4()),
                'ssn_number': ssn_number,
                'wages_and_compensation': wages_and_compensation
            }
        )

        print(f"Data stored in DynamoDB:, ssn_number={ssn_number}, wages_and_compensation={wages_and_compensation}")

    except Exception as e:
        print(f"Error processing file {object_key} from bucket {bucket_name}: {str(e)}")
        raise e