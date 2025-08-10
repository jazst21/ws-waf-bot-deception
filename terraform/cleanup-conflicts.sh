#!/bin/bash

# Script to clean up conflicting AWS resources before Terraform deployment

set -e

echo "Cleaning up conflicting AWS resources..."

# Remove existing Lambda permission
echo "Removing existing Lambda permission..."
aws lambda remove-permission \
  --function-name bot-deception-dev-api \
  --statement-id AllowExecutionFromALB \
  --region us-east-1 || echo "Lambda permission not found or already removed"

# Get CloudFront function ETag and delete it
echo "Removing existing CloudFront function..."
ETAG=$(aws cloudfront describe-function \
  --name bot-deception-dev-bot-redirect \
  --query 'ETag' \
  --output text 2>/dev/null || echo "")

if [ ! -z "$ETAG" ]; then
  aws cloudfront delete-function \
    --name bot-deception-dev-bot-redirect \
    --if-match "$ETAG" || echo "CloudFront function not found or already removed"
else
  echo "CloudFront function not found or already removed"
fi

echo "Cleanup completed successfully!"
