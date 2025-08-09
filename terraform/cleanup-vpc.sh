#!/bin/bash

# Specific script to clean up VPC resources that cause subnet conflicts
# This addresses the "CIDR conflicts with another subnet" errors

set -e

echo "🌐 VPC Cleanup Script - Resolving subnet CIDR conflicts"

NAME_PREFIX="bot-deception-dev"

# Function to wait for resource deletion
wait_for_deletion() {
    local resource_type="$1"
    local check_command="$2"
    local max_wait=60
    local wait_time=0
    
    echo "    ⏳ Waiting for $resource_type deletion..."
    while [ $wait_time -lt $max_wait ]; do
        if ! eval "$check_command" >/dev/null 2>&1; then
            echo "    ✅ $resource_type deleted"
            return 0
        fi
        sleep 5
        wait_time=$((wait_time + 5))
        echo "    ⏳ Still waiting for $resource_type deletion... (${wait_time}s)"
    done
    echo "    ⚠️  Timeout waiting for $resource_type deletion, continuing..."
}

# Find the VPC
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=tag:Name,Values=bot-deception" --query 'Vpcs[0].VpcId' --output text 2>/dev/null || echo "")

if [ -z "$VPC_ID" ] || [ "$VPC_ID" == "None" ]; then
    echo "🔍 No VPC found with name 'bot-deception', checking for any VPC with our subnets..."
    
    # Look for VPCs that contain our CIDR blocks
    VPC_ID=$(aws ec2 describe-subnets --filters "Name=cidr-block,Values=10.0.0.0/24" --query 'Subnets[0].VpcId' --output text 2>/dev/null || echo "")
    
    if [ -z "$VPC_ID" ] || [ "$VPC_ID" == "None" ]; then
        echo "✅ No conflicting VPC/subnets found"
        exit 0
    fi
fi

echo "🎯 Found VPC: $VPC_ID"
echo "🧹 Starting comprehensive VPC cleanup..."

# 1. Delete Load Balancers first (they use subnets)
echo "⚖️  Deleting Load Balancers..."
aws elbv2 describe-load-balancers --query "LoadBalancers[?contains(LoadBalancerName, '$NAME_PREFIX')].LoadBalancerArn" --output text | while read lb_arn; do
    if [ ! -z "$lb_arn" ]; then
        echo "    Deleting Load Balancer: $lb_arn"
        aws elbv2 delete-load-balancer --load-balancer-arn "$lb_arn" 2>/dev/null || true
    fi
done

# Wait for load balancers to be deleted
sleep 30

# 2. Delete NAT Gateways (they use subnets and EIPs)
echo "🌐 Deleting NAT Gateways..."
aws ec2 describe-nat-gateways --filter "Name=vpc-id,Values=$VPC_ID" --query 'NatGateways[?State==`available`].NatGatewayId' --output text | while read nat_id; do
    if [ ! -z "$nat_id" ]; then
        echo "    Deleting NAT Gateway: $nat_id"
        aws ec2 delete-nat-gateway --nat-gateway-id "$nat_id" 2>/dev/null || true
    fi
done

# Wait for NAT gateways to be deleted
wait_for_deletion "NAT Gateways" "aws ec2 describe-nat-gateways --filter 'Name=vpc-id,Values=$VPC_ID' --query 'NatGateways[?State==\`available\`]' --output text | grep -q ."

# 3. Delete Route Table Associations
echo "🛣️  Deleting Route Table Associations..."
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC_ID" --query 'RouteTables[].Associations[?!Main].RouteTableAssociationId' --output text | while read assoc_id; do
    if [ ! -z "$assoc_id" ]; then
        echo "    Deleting route table association: $assoc_id"
        aws ec2 disassociate-route-table --association-id "$assoc_id" 2>/dev/null || true
    fi
done

# 4. Delete Custom Route Tables
echo "🛣️  Deleting Custom Route Tables..."
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC_ID" --query 'RouteTables[?!Associations[0].Main].RouteTableId' --output text | while read rt_id; do
    if [ ! -z "$rt_id" ]; then
        echo "    Deleting route table: $rt_id"
        aws ec2 delete-route-table --route-table-id "$rt_id" 2>/dev/null || true
    fi
done

# 5. Delete Network Interfaces (ENIs) that might be attached to subnets
echo "🔌 Deleting Network Interfaces..."
aws ec2 describe-network-interfaces --filters "Name=vpc-id,Values=$VPC_ID" --query 'NetworkInterfaces[?Status==`available`].NetworkInterfaceId' --output text | while read eni_id; do
    if [ ! -z "$eni_id" ]; then
        echo "    Deleting network interface: $eni_id"
        aws ec2 delete-network-interface --network-interface-id "$eni_id" 2>/dev/null || true
    fi
done

# 6. Delete Subnets (the main source of conflict)
echo "🏠 Deleting Subnets..."
SUBNET_CIDRS=("10.0.0.0/24" "10.0.1.0/24" "10.0.2.0/24" "10.0.3.0/24")

for cidr in "${SUBNET_CIDRS[@]}"; do
    SUBNET_ID=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" "Name=cidr-block,Values=$cidr" --query 'Subnets[0].SubnetId' --output text 2>/dev/null || echo "")
    if [ ! -z "$SUBNET_ID" ] && [ "$SUBNET_ID" != "None" ]; then
        echo "    Deleting subnet $cidr: $SUBNET_ID"
        aws ec2 delete-subnet --subnet-id "$SUBNET_ID" 2>/dev/null || true
    fi
done

# 7. Delete Internet Gateway
echo "🌍 Deleting Internet Gateway..."
aws ec2 describe-internet-gateways --filters "Name=attachment.vpc-id,Values=$VPC_ID" --query 'InternetGateways[].InternetGatewayId' --output text | while read igw_id; do
    if [ ! -z "$igw_id" ]; then
        echo "    Detaching and deleting internet gateway: $igw_id"
        aws ec2 detach-internet-gateway --internet-gateway-id "$igw_id" --vpc-id "$VPC_ID" 2>/dev/null || true
        aws ec2 delete-internet-gateway --internet-gateway-id "$igw_id" 2>/dev/null || true
    fi
done

# 8. Delete Security Groups (except default)
echo "🔒 Deleting Security Groups..."
aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID" --query 'SecurityGroups[?GroupName!=`default`].GroupId' --output text | while read sg_id; do
    if [ ! -z "$sg_id" ]; then
        echo "    Deleting security group: $sg_id"
        aws ec2 delete-security-group --group-id "$sg_id" 2>/dev/null || true
    fi
done

# 9. Delete the VPC
echo "🏢 Deleting VPC..."
aws ec2 delete-vpc --vpc-id "$VPC_ID" 2>/dev/null || true

# 10. Release any unassociated Elastic IPs
echo "💰 Releasing unassociated Elastic IPs..."
aws ec2 describe-addresses --query 'Addresses[?AssociationId==null].AllocationId' --output text | while read alloc_id; do
    if [ ! -z "$alloc_id" ]; then
        echo "    Releasing EIP: $alloc_id"
        aws ec2 release-address --allocation-id "$alloc_id" 2>/dev/null || true
    fi
done

echo ""
echo "✅ VPC cleanup completed!"
echo "🚀 Subnet CIDR conflicts should now be resolved"
echo "💡 You can now run terraform apply to create fresh networking resources"
