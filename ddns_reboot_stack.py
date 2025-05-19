import os
import aws_cdk as cdk
from constructs import Construct
import aws_cdk.aws_iam as iam
import aws_cdk.aws_lambda as lambda_
import aws_cdk.aws_events as events
import aws_cdk.aws_events_targets as targets
from aws_cdk.aws_lambda_python_alpha import PythonFunction


class DdnsRebootStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get the hosted zone ID from context
        hosted_zone_id = self.node.try_get_context('hosted_zone_id')
        if not hosted_zone_id:
            raise ValueError('Hosted Zone ID must be provided as an option: hosted_zone_id')

        # Optional default DNS prefix for instances without a specific name
        default_dns_prefix = self.node.try_get_context('default_dns_prefix') or 'ec2-instance'

        # Create a single Lambda function for DNS management
        dns_manager_lambda = PythonFunction(self, 'DnsManagerLambda',
            entry=os.path.join(os.path.dirname(__file__), 'lambda'),
            index='dns_manager.py',
            runtime=lambda_.Runtime.PYTHON_3_9,
            timeout=cdk.Duration.minutes(2),
            environment={
                'HOSTED_ZONE_ID': hosted_zone_id,
                'DEFAULT_DNS_PREFIX': default_dns_prefix,
            },
            description='Lambda function that updates Route 53 DNS records based on EC2 instance IP_Tracking tags',
        )

        # Grant Lambda permissions to access EC2 and Route 53
        lambda_policy = iam.PolicyStatement(
            actions=[
                'route53:ChangeResourceRecordSets',
                'route53:ListResourceRecordSets',
                'route53:GetHostedZone',
                'ec2:DescribeInstances',
            ],
            resources=['*']  # For simplicity, but consider restricting this in production
        )

        dns_manager_lambda.add_to_role_policy(lambda_policy)

        # Create CloudWatch Event Rule for EC2 state change with tag-based filtering
        # Since CloudWatch Events doesn't directly support filtering by tag presence in the event pattern for EC2 state changes,
        # we'll create a rule that triggers on running state and then filter in the Lambda function
        state_change_rule = events.Rule(self, 'EC2StateChangeRule',
            event_pattern=events.EventPattern(
                source=['aws.ec2'],
                detail_type=['EC2 Instance State-change Notification'],
                detail={
                    'state': ['running'],  # Only trigger on 'running' state
                }
            ),
            description='Rule that triggers when EC2 instances enter the running state',
        )

        # Create CloudWatch Event Rule for EC2 instance launch events
        instance_launch_rule = events.Rule(self, 'EC2InstanceLaunchRule',
            event_pattern=events.EventPattern(
                source=['aws.ec2'],
                detail_type=['EC2 Instance Launch Successful'],
            ),
            description='Rule that triggers when EC2 instances are launched successfully',
        )

        # Create CloudWatch Event Rule for tag changes specifically for the IP_Tracking tag
        tag_change_rule = events.Rule(self, 'TagChangeRule',
            event_pattern=events.EventPattern(
                source=['aws.tag'],
                detail_type=['Tag Change on Resource'],
                detail={
                    'service': ['ec2'],
                    'resource-type': ['instance'],
                    # We don't filter by exact tag key name here since we want to match case-insensitive
                    # The Lambda function will handle the case-insensitive matching
                }
            ),
            description='Rule that triggers when the IP_Tracking tag is changed on EC2 instances',
        )

        # Add Lambda function as target for all CloudWatch Events
        state_change_rule.add_target(targets.LambdaFunction(dns_manager_lambda))
        instance_launch_rule.add_target(targets.LambdaFunction(dns_manager_lambda))
        tag_change_rule.add_target(targets.LambdaFunction(dns_manager_lambda))

        # Output important information
        cdk.CfnOutput(self, 'DnsManagerLambdaArn',
            value=dns_manager_lambda.function_arn,
            description='ARN of the DNS Manager Lambda function'
        )

        cdk.CfnOutput(self, 'HostedZoneId',
            value=hosted_zone_id,
            description='Route 53 Hosted Zone ID used for DNS updates'
        )

        cdk.CfnOutput(self, 'DefaultDnsPrefix',
            value=default_dns_prefix,
            description='Default DNS prefix used for instances without a specific name in the IP_Tracking tag'
        )