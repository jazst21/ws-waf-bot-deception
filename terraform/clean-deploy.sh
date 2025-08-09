#!/bin/bash

# Clean deployment script for CodeBuild
# This script handles the "already exists" problem by doing a clean destroy/create cycle

set -e

echo "🧹 Starting clean deployment process..."

# Function to safely destroy resources
safe_destroy() {
    echo "🗑️  Attempting to destroy existing resources..."
    terraform destroy -auto-approve 2>/dev/null || {
        echo "⚠️  Destroy failed or no resources to destroy, continuing..."
    }
}

# Function to clean up any orphaned resources
cleanup_orphaned_resources() {
    echo "🧽 Cleaning up any orphaned AWS resources..."
    
    # Clean up CloudFront OACs
    aws cloudfront list-origin-access-controls --query "OriginAccessControlList.Items[?contains(Name, 'bot-deception-dev')].Id" --output text | while read oac_id; do
        if [ ! -z "$oac_id" ] && [ "$oac_id" != "None" ]; then
            echo "  Deleting CloudFront OAC: $oac_id"
            aws cloudfront delete-origin-access-control --id "$oac_id" 2>/dev/null || true
        fi
    done
    
    # Clean up WAF IP Sets
    aws wafv2 list-ip-sets --scope CLOUDFRONT --query "IPSets[?contains(Name, 'bot-deception-dev')].Id" --output text | while read ip_set_id; do
        if [ ! -z "$ip_set_id" ] && [ "$ip_set_id" != "None" ]; then
            echo "  Deleting WAF IP Set: $ip_set_id"
            # Get lock token first
            LOCK_TOKEN=$(aws wafv2 get-ip-set --scope CLOUDFRONT --id "$ip_set_id" --query 'LockToken' --output text 2>/dev/null || echo "")
            if [ ! -z "$LOCK_TOKEN" ]; then
                aws wafv2 delete-ip-set --scope CLOUDFRONT --id "$ip_set_id" --lock-token "$LOCK_TOKEN" 2>/dev/null || true
            fi
        fi
    done
    
    echo "✅ Cleanup completed"
}

# Main deployment logic
echo "📋 Initializing Terraform..."
terraform init

if [ "$1" == "clean" ]; then
    echo "🧹 Clean deployment requested"
    safe_destroy
    cleanup_orphaned_resources
    sleep 10  # Wait for AWS eventual consistency
fi

echo "🚀 Starting fresh deployment..."
terraform plan -detailed-exitcode
PLAN_EXIT_CODE=$?

if [ $PLAN_EXIT_CODE -eq 0 ]; then
    echo "✅ No changes needed."
elif [ $PLAN_EXIT_CODE -eq 2 ]; then
    echo "📦 Changes detected, applying..."
    terraform apply -auto-approve
    echo "✅ Deployment completed successfully!"
else
    echo "❌ Terraform plan failed with exit code: $PLAN_EXIT_CODE"
    exit 1
fi
