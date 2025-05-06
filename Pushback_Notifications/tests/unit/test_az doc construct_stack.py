import aws_cdk as core
import aws_cdk.assertions as assertions

from az doc construct.az doc construct_stack import AzDocConstructStack

# example tests. To run these tests, uncomment this file along with the example
# resource in az doc construct/az doc construct_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AzDocConstructStack(app, "az-doc-construct")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
