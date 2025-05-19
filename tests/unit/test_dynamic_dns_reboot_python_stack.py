import aws_cdk as core
import aws_cdk.assertions as assertions

from dynamic_dns_reboot_python.dynamic_dns_reboot_python_stack import DynamicDnsRebootPythonStack

# example tests. To run these tests, uncomment this file along with the example
# resource in dynamic_dns_reboot_python/dynamic_dns_reboot_python_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = DynamicDnsRebootPythonStack(app, "dynamic-dns-reboot-python")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
