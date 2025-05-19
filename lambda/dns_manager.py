import boto3
import os
import json

def handler(event, context):
    """
    Lambda handler that processes EC2 events and updates Route53 DNS records
    based on the IP_Tracking tag.
    """
    print(f"Received event: {json.dumps(event)}")
    
    # Extract instance ID based on event type
    instance_id = None
    
    if 'detail-type' in event:
        if event['detail-type'] == 'EC2 Instance State-change Notification':
            # Skip if instance is not running
            if event['detail']['state'] != 'running':
                print(f"Instance {event['detail']['instance-id']} is not running. Skipping.")
                return
            instance_id = event['detail']['instance-id']
        elif event['detail-type'] == 'EC2 Instance Launch Successful':
            instance_id = event['detail']['instance-id']
        elif event['detail-type'] == 'Tag Change on Resource':
            if event['detail'].get('resource-type') == 'instance':
                instance_id = event['resources'][0].split('/')[-1]
    
    if not instance_id:
        print("Could not extract instance ID from event. Skipping.")
        return
    
    print(f"Processing instance: {instance_id}")
    
    # Initialize clients
    ec2_client = boto3.client('ec2')
    route53_client = boto3.client('route53')
    hosted_zone_id = os.environ['HOSTED_ZONE_ID']
    default_dns_prefix = os.environ.get('DEFAULT_DNS_PREFIX', 'ec2-instance')
    
    # Get hosted zone details
    try:
        hosted_zone = route53_client.get_hosted_zone(Id=hosted_zone_id)
        zone_name = hosted_zone['HostedZone']['Name']
    except Exception as e:
        print(f"Error getting hosted zone details: {e}")
        return
    
    # Get instance details
    try:
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        if not response['Reservations']:
            print(f"No reservation found for instance {instance_id}")
            return
        
        instance = response['Reservations'][0]['Instances'][0]
        current_ip = instance.get('PublicIpAddress')
        
        if not current_ip:
            print(f"Instance {instance_id} does not have a public IP address. Skipping.")
            return
        
        # Check for IP_Tracking tag (case-insensitive)
        ip_tracking_tag = next((tag for tag in instance.get('Tags', []) if tag['Key'].lower() == 'ip_tracking'), None)
        
        if not ip_tracking_tag:
            print(f"Instance {instance_id} does not have the IP_Tracking tag. Skipping.")
            return
        
        # Determine DNS name from tag value
        dns_name = ip_tracking_tag.get('Value', '').strip()
        if not dns_name:
            dns_name = f"{default_dns_prefix}-{instance_id}.{zone_name}"
        elif '.' not in dns_name:
            dns_name = f"{dns_name}.{zone_name}"
        elif not dns_name.endswith('.'):
            dns_name = f"{dns_name}."
        
        # Validate DNS name belongs to our hosted zone
        if not dns_name.endswith(zone_name):
            print(f"DNS name {dns_name} is not in the managed zone {zone_name}. Skipping.")
            return
        
        # Check if record exists and needs updating
        try:
            record_sets = route53_client.list_resource_record_sets(
                HostedZoneId=hosted_zone_id,
                StartRecordName=dns_name,
                StartRecordType='A',
                MaxItems='1'
            )
            
            record_exists = False
            for record in record_sets['ResourceRecordSets']:
                if record['Name'] == dns_name and record['Type'] == 'A':
                    record_exists = True
                    if len(record['ResourceRecords']) == 1 and record['ResourceRecords'][0]['Value'] == current_ip:
                        print(f"DNS record {dns_name} already points to {current_ip}. No update needed.")
                        return
                    break
            
            # Update or create the DNS record
            response = route53_client.change_resource_record_sets(
                HostedZoneId=hosted_zone_id,
                ChangeBatch={
                    'Changes': [{
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': dns_name,
                            'Type': 'A',
                            'TTL': 300,
                            'ResourceRecords': [{'Value': current_ip}]
                        }
                    }]
                }
            )
            
            action = "Updated" if record_exists else "Created"
            print(f"{action} DNS record {dns_name} with IP {current_ip} for instance {instance_id}")
            
        except Exception as e:
            print(f"Error managing DNS record: {e}")
            
    except Exception as e:
        print(f"Error processing instance {instance_id}: {e}")