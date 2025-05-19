# Dynamic DNS Reboot

This project implements a serverless Dynamic DNS solution using AWS CDK, Lambda, and CloudWatch Events. It monitors EC2 state changes and tag changes, automatically updating Route 53 DNS records when instances receive new public IP addresses.

## Features

- Automatically updates Route 53 DNS records when EC2 instances start
- Monitors tag changes on EC2 instances in real-time
- Uses the IP_Tracking tag value directly as the DNS name to update
- Creates DNS records automatically for tagged instances
- Supports default naming for instances without a specific DNS name in the tag

## Prerequisites

- AWS CLI configured with appropriate permissions
- Python 3.9 or later
- AWS CDK CLI installed
- Required Python packages (installed via virtual environment)

## Project Structure

```
.
├── app.py
├── cdk.json
├── cdk.out/
├── ddns_reboot_stack.py
├── dynamic_dns_reboot_python/
│   ├── __init__.py
│   └── dynamic_dns_reboot_python_stack.py
├── lambda/
│   ├── dns_manager.py
│   ├── track_tag.py
│   └── update_dns.py
├── requirements-dev.txt
├── requirements.txt
├── tests/
│   ├── __init__.py
│   └── unit/
│       ├── __init__.py
│       └── test_dynamic_dns_reboot_python_stack.py
└── README.md
```

## Setup

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/dynamic-dns-tag-monitoring.git
   cd dynamic-dns-tag-monitoring
   ```

2. Set up a Python virtual environment:
   ```
   # Create a virtual environment
   python3 -m venv .venv
   
   # Activate the virtual environment
   # On Windows:
   .venv\Scripts\activate
   
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```
   # Install runtime dependencies
   pip install -r requirements.txt
   
   # Install development dependencies (optional)
   pip install -r requirements-dev.txt
   ```

4. Deploy the stack:
   ```
   cdk deploy -c hosted_zone_id=YOUR_HOSTED_ZONE_ID -c default_dns_prefix=YOUR_PREFIX
   ```
   Replace:
   - `YOUR_HOSTED_ZONE_ID` with your actual Route 53 Hosted Zone ID
   - `YOUR_PREFIX` (optional) with your preferred default prefix for instances without a specific DNS name

## Usage

Tag EC2 instances with the `IP_Tracking` tag to enroll them in automatic DNS management:

### Tag Format Options

1. **Full domain name**:
   ```
   Key: IP_Tracking
   Value: myserver.example.com
   ```

2. **Simple hostname** (will be automatically expanded with your hosted zone):
   ```
   Key: IP_Tracking
   Value: myserver
   ```

3. **Empty value or no tag**:
   If the tag value is empty or the tag is not present, a default name will be used:
   ```
   {default_dns_prefix}-{instance_id}.{your_domain}
   ```
   For example: `ec2-instance-i-1234abcd.example.com`

The system will automatically:
- Update DNS records when tagged instances start
- Update DNS records when the IP_Tracking tag is added or modified
- Create new DNS records if they don't exist
- Only update records when the IP has actually changed

## How It Works

1. When an EC2 instance starts or has its tags modified:
   - The Lambda function is triggered by CloudWatch Events
   - It checks if the instance has the IP_Tracking tag
   - It gets the instance's current public IP address
   - It creates or updates the Route 53 A record

2. The solution is completely self-managing:
   - No manual intervention required after setup
   - Any EC2 instance with the proper tag is automatically enrolled
   - DNS records are only updated when necessary

## Development

When working on this project, make sure your virtual environment is activated:

```
# On Windows:
.venv\Scripts\activate

# On macOS/Linux:
 source .venv/bin/activate
```

To run tests:

```
python3 -m pytest
```

To synthesize the CloudFormation template for this code:

```
cdk synth
```

## Troubleshooting

- Check CloudWatch Logs for the Lambda function to debug issues
- Ensure the `IP_Tracking` tag value is a valid DNS name in your hosted zone
- Verify that the provided Hosted Zone ID is correct and accessible
- Make sure instances have public IP addresses
- If you encounter dependency issues, verify your virtual environment is activated

## Clean Up

To remove all resources created by this stack:

```
cdk destroy
```

## Security Considerations

- The Lambda function has permissions to modify Route 53 records in the specified hosted zone
- Consider implementing additional validation for the DNS names in the tag values
- Review the IAM permissions to ensure they follow the principle of least privilege
- Keep your dependencies updated to avoid security vulnerabilities

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Set up your development environment as described in the Setup section
4. Make your changes
5. Run tests to ensure your changes don't break existing functionality
6. Commit your changes (`git commit -m 'Add some amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request