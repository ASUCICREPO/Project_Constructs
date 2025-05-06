from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_dynamodb as dynamodb,
    aws_apigatewayv2 as apigatewayv2,
    App,
    Duration,
    
)
from aws_cdk.aws_apigatewayv2_integrations import WebSocketLambdaIntegration
from constructs import Construct
from aws_cdk.aws_iam import PolicyStatement

class PushbackNotifications(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        websocket_api = apigatewayv2.WebSocketApi(
            self, "Pushback Lambda WebSocket API",
            api_name="Pushback Lambda WebSocket API",
            description="WebSocket API for real-time updates"
        )
        
        events_table = dynamodb.Table(
            self, "EventsTable",
            partition_key={"name": "primary_key", "type": dynamodb.AttributeType.STRING},
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST
        )
        
        process_events_lambda = _lambda.Function(
            self, "ProcessEventsLambda",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_docker_build("lambda/processevents"),
            environment={
                "TABLE_NAME": events_table.table_name,
                "WEBSOCKET_URL": websocket_api.api_endpoint,
                "REGION":self.region
            },
            timeout=Duration.seconds(600)
        )
        process_events_lambda.add_to_role_policy(
            PolicyStatement(
                actions=["execute-api:ManageConnections"],
                resources=[
                    f"arn:aws:execute-api:{self.region}:{self.account}:{websocket_api.api_id}/cdk_test/POST/@connections/*"
                ]
            )
        )
        events_table.grant_read_write_data(process_events_lambda)

        connect_integration = WebSocketLambdaIntegration(
            "ConnectIntegration",
            handler=process_events_lambda
        )
        disconnect_integration = WebSocketLambdaIntegration(
            "DisconnectIntegration",
            handler=process_events_lambda
        )
        default_integration = WebSocketLambdaIntegration(
            "DefaultIntegration",
            handler=process_events_lambda
        )

        websocket_api.add_route(
            route_key="$connect",
            integration=connect_integration
        )
        websocket_api.add_route(
            route_key="$disconnect",
            integration=disconnect_integration
        )
        websocket_api.add_route(
            route_key="$default",
            integration=default_integration
        )

        apigatewayv2.WebSocketStage(
            self, "ProdStage",
            web_socket_api=websocket_api,
            stage_name="cdk_test",
            auto_deploy=True
        )

    

app = App()
PushbackNotifications(app, "PushbackNotifications")
app.synth()