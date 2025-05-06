import aws_cdk as core
import aws_cdk.assertions as assertions

from water_bot construct.water_bot construct_stack import WaterBotConstructStack

# example tests. To run these tests, uncomment this file along with the example
# resource in water_bot construct/water_bot construct_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = WaterBotConstructStack(app, "water-bot-construct")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
