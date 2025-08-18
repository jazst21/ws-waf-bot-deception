#!/bin/bash

echo "Monitoring VPC Origin deployment status..."

# Function to check VPC Origin status
check_vpc_origin_status() {
    aws cloudfront list-vpc-origins --region us-east-1 --query 'VpcOriginList.Items[0].Status' --output text
}

# Wait for VPC Origin to be deployed
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    status=$(check_vpc_origin_status)
    echo "Attempt $attempt/$max_attempts: VPC Origin status is '$status'"
    
    if [ "$status" = "Deployed" ]; then
        echo "VPC Origin is now deployed! Applying Terraform changes..."
        terraform apply -auto-approve
        exit $?
    elif [ "$status" = "Failed" ]; then
        echo "VPC Origin deployment failed!"
        exit 1
    fi
    
    echo "Waiting 30 seconds before next check..."
    sleep 30
    attempt=$((attempt + 1))
done

echo "Timeout waiting for VPC Origin deployment after $((max_attempts * 30)) seconds"
exit 1
