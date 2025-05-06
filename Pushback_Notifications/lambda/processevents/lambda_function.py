import json
import boto3
import uuid
from boto3.dynamodb.conditions import Key
import boto3
import os

dynamodb = boto3.resource('dynamodb')
REGION = os.getenv("REGION")
WEBSOCKET_URL = os.getenv("WEBSOCKET_URL")
WEBSOCKET_HTTPS_URL = f"https://{WEBSOCKET_URL.split('//')[1]}/cdk_test/"
TABLE_NAME = os.environ['TABLE_NAME']
apigatewaymanagementapi = boto3.client('apigatewaymanagementapi', 
    endpoint_url=WEBSOCKET_HTTPS_URL)  

# function to add the connection id of a client to the database
def handle_websocket_connections(event):
    try:
        if 'requestContext' not in event:
            connection_id = event['connectionId']
            send_to_connection(connection_id)
            return {
                'statusCode': 200,
                'body': 'Done'
            }
        table = dynamodb.Table(TABLE_NAME)
        connection_id = event['requestContext']['connectionId']
        event_type = event['requestContext']['eventType']
        if event_type == 'CONNECT':
            primary_key = str(uuid.uuid4())
            table.put_item(Item={'connectionId': connection_id, 'primary_key': primary_key})
            
            return {
                    'statusCode': 200,
                    'body': json.dumps(f'Added to database successfully')
                }

        elif event_type == 'DISCONNECT':
            response = table.scan(
                    FilterExpression=Key('connectionId').eq(connection_id)
            )
            items = response.get('Items', [])
            if not items:
                print(f"No items found with connectionId: {connection_id}")
                return
            for item in items:
                table.delete_item(
                    Key={
                        'primary_key': item['primary_key']  
                    }
                )

        elif event_type == 'MESSAGE':
            message = {
                "message": f"Hi! {connection_id}"
            }
            apigatewaymanagementapi.post_to_connection(
                ConnectionId=connection_id,
                Data=json.dumps(message)
            )
        else:
            return {
                'statusCode': 500,
                'body': 'Bad request'
                }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }
            

def send_to_connection(connection_id):
    try:
        apigatewaymanagementapi.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(f"Hello connection, message received")
        )
    except Exception as e:
        print("Thr exeption is: ", e)
        pass

def lambda_handler(event, context):
    return handle_websocket_connections(event)
    