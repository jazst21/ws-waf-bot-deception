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
    
    NAME_PREFIX="bot-deception-dev"
    
    # Clean up CloudFront OACs
    echo "  🌩️  Cleaning CloudFront OACs..."
    aws cloudfront list-origin-access-controls --query "OriginAccessControlList.Items[?contains(Name, '$NAME_PREFIX')].Id" --output text | while read oac_id; do
        if [ ! -z "$oac_id" ] && [ "$oac_id" != "None" ]; then
            echo "    Deleting CloudFront OAC: $oac_id"
            aws cloudfront delete-origin-access-control --id "$oac_id" 2>/dev/null || true
        fi
    done
    
    # Clean up WAF resources
    echo "  🛡️  Cleaning WAF resources..."
    
    # Delete Web ACL first (it references IP sets)
    WEB_ACL_ID=$(aws wafv2 list-web-acls --scope CLOUDFRONT --query "WebACLs[?Name=='$NAME_PREFIX-web-acl'].Id" --output text 2>/dev/null || echo "")
    if [ ! -z "$WEB_ACL_ID" ] && [ "$WEB_ACL_ID" != "None" ]; then
        echo "    Deleting WAF Web ACL: $WEB_ACL_ID"
        LOCK_TOKEN=$(aws wafv2 get-web-acl --scope CLOUDFRONT --id "$WEB_ACL_ID" --query 'LockToken' --output text 2>/dev/null || echo "")
        if [ ! -z "$LOCK_TOKEN" ]; then
            aws wafv2 delete-web-acl --scope CLOUDFRONT --id "$WEB_ACL_ID" --lock-token "$LOCK_TOKEN" 2>/dev/null || true
        fi
    fi
    
    # Clean up WAF IP Sets
    aws wafv2 list-ip-sets --scope CLOUDFRONT --query "IPSets[?contains(Name, '$NAME_PREFIX')].Id" --output text | while read ip_set_id; do
        if [ ! -z "$ip_set_id" ] && [ "$ip_set_id" != "None" ]; then
            echo "    Deleting WAF IP Set: $ip_set_id"
            LOCK_TOKEN=$(aws wafv2 get-ip-set --scope CLOUDFRONT --id "$ip_set_id" --query 'LockToken' --output text 2>/dev/null || echo "")
            if [ ! -z "$LOCK_TOKEN" ]; then
                aws wafv2 delete-ip-set --scope CLOUDFRONT --id "$ip_set_id" --lock-token "$LOCK_TOKEN" 2>/dev/null || true
            fi
        fi
    done
    
    # Clean up VPC resources (most critical for subnet conflicts)
    echo "  🌐 Cleaning VPC resources..."
    
    VPC_ID=$(aws ec2 describe-vpcs --filters "Name=tag:Name,Values=bot-deception" --query 'Vpcs[0].VpcId' --output text 2>/dev/null || echo "")
    if [ ! -z "$VPC_ID" ] && [ "$VPC_ID" != "None" ]; then
        echo "    Found VPC: $VPC_ID, cleaning associated resources..."
        
        # Delete NAT Gateways first
        aws ec2 describe-nat-gateways --filter "Name=vpc-id,Values=$VPC_ID" --query 'NatGateways[?State==`available`].NatGatewayId' --output text | while read nat_id; do
            if [ ! -z "$nat_id" ]; then
                echo "      Deleting NAT Gateway: $nat_id"
                aws ec2 delete-nat-gateway --nat-gateway-id "$nat_id" 2>/dev/null || true
            fi
        done
        
        # Wait for NAT gateways to be deleted
        echo "      Waiting for NAT gateways to be deleted..."
        sleep 30
        
        # Delete route table associations
        aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC_ID" --query 'RouteTables[].Associations[?!Main].RouteTableAssociationId' --output text | while read assoc_id; do
            if [ ! -z "$assoc_id" ]; then
                echo "      Deleting route table association: $assoc_id"
                aws ec2 disassociate-route-table --association-id "$assoc_id" 2>/dev/null || true
            fi
        done
        
        # Delete custom route tables
        aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC_ID" --query 'RouteTables[?!Associations[0].Main].RouteTableId' --output text | while read rt_id; do
            if [ ! -z "$rt_id" ]; then
                echo "      Deleting route table: $rt_id"
                aws ec2 delete-route-table --route-table-id "$rt_id" 2>/dev/null || true
            fi
        done
        
        # Delete subnets
        aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[].SubnetId' --output text | while read subnet_id; do
            if [ ! -z "$subnet_id" ]; then
                echo "      Deleting subnet: $subnet_id"
                aws ec2 delete-subnet --subnet-id "$subnet_id" 2>/dev/null || true
            fi
        done
        
        # Delete internet gateway
        aws ec2 describe-internet-gateways --filters "Name=attachment.vpc-id,Values=$VPC_ID" --query 'InternetGateways[].InternetGatewayId' --output text | while read igw_id; do
            if [ ! -z "$igw_id" ]; then
                echo "      Detaching and deleting internet gateway: $igw_id"
                aws ec2 detach-internet-gateway --internet-gateway-id "$igw_id" --vpc-id "$VPC_ID" 2>/dev/null || true
                aws ec2 delete-internet-gateway --internet-gateway-id "$igw_id" 2>/dev/null || true
            fi
        done
        
        # Delete security groups (except default)
        aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID" --query 'SecurityGroups[?GroupName!=`default`].GroupId' --output text | while read sg_id; do
            if [ ! -z "$sg_id" ]; then
                echo "      Deleting security group: $sg_id"
                aws ec2 delete-security-group --group-id "$sg_id" 2>/dev/null || true
            fi
        done
        
        # Finally delete the VPC
        echo "      Deleting VPC: $VPC_ID"
        aws ec2 delete-vpc --vpc-id "$VPC_ID" 2>/dev/null || true
        
        # Release any remaining Elastic IPs
        aws ec2 describe-addresses --query 'Addresses[?AssociationId==null].AllocationId' --output text | while read alloc_id; do
            if [ ! -z "$alloc_id" ]; then
                echo "      Releasing EIP: $alloc_id"
                aws ec2 release-address --allocation-id "$alloc_id" 2>/dev/null || true
            fi
        done
    fi
    
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
