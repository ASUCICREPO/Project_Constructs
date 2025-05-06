from constructs import Construct
import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_ecs_patterns as ecs_patterns,
    aws_ecr_assets as ecr_assets
)
from aws_cdk.aws_ecs import ContainerImage
from aws_cdk.aws_ec2 import SecurityGroup, Port, Peer

class ECRECSLoadBalancer(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        vpc = ec2.Vpc(self, "VPC", max_azs=2)
        
        alb_security_group = SecurityGroup(
            self, "ALBSecurityGroup",
            vpc=vpc,
            allow_all_outbound=True,  
            description="Security group for ALB"
        )
        # Allow inbound HTTP traffic
        alb_security_group.add_ingress_rule(
            peer=Peer.any_ipv4(),
            connection=Port.all_traffic(),
            description="Allow inbound HTTP traffic"
        )

        # Allow inbound HTTPS traffic (optional)
        alb_security_group.add_ingress_rule(
            peer=Peer.any_ipv4(),
            connection=Port.all_traffic(),
            description="Allow inbound HTTPS traffic"
        )
        ecs_task_security_group = SecurityGroup(
            self, "ECSTaskSecurityGroup",
            vpc=vpc,
            allow_all_outbound=True,  # Allow all outbound traffic
            description="Security group for ECS tasks"
        )

        # Allow inbound traffic from ALB security group
        ecs_task_security_group.add_ingress_rule(
            peer=alb_security_group,
            connection=Port.all_traffic(),
            description="Allow traffic from ALB"
        )
        # Build and push Docker image to ECR
        docker_image = ecr_assets.DockerImageAsset(
            self, "DockerImageAsset",
            directory="./docker",  # Path to the directory containing Dockerfile
        )

        # Use the Docker image as a container image in ECS
        container_image = ContainerImage.from_docker_image_asset(docker_image)

        # Define the task definition with the Docker image
        task_definition = ecs.FargateTaskDefinition(
            self, "TaskDefinition",
            memory_limit_mib=512,
            cpu=256
        )
        container = task_definition.add_container(
            "WaterbotContainer",
            image=container_image,
            logging=ecs.LogDriver.aws_logs(stream_prefix="Logs"),
            environment={
                "ENV_VAR_KEY": "ENV_VAR_VALUE"  # Add necessary environment variables
            }
        )

        # Map container port to host port (e.g., 80 to 80)
        container.add_port_mappings(
            ecs.PortMapping(container_port=80, protocol=ecs.Protocol.TCP)
        )        

        # Create ECS Cluster
        cluster = ecs.Cluster(
            self, "FargateCluster",
            vpc=vpc
        )

        # Instantiate the ECS service with ALB
        ecs_service = ecs_patterns.ApplicationLoadBalancedFargateService(self, "FargateService",
            cluster=cluster,
            task_definition=task_definition,
            desired_count=1,
            listener_port=80,
            security_groups = [alb_security_group]
        )
        ecs_service.service.connections.add_security_group(ecs_task_security_group)


app = cdk.App()
ECRECSLoadBalancer(app, "ECRECSLoadBalancer")
app.synth()
