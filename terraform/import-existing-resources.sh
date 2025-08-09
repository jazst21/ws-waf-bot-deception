#!/bin/bash

# Comprehensive script to import all existing AWS resources
# This prevents "already exists" errors in CodeBuild retries

set -e

echo "🔍 Scanning for existing AWS resources to import..."

# Get the name prefix from terraform variables
NAME_PREFIX="bot-deception-dev"

# Function to safely import a resource
safe_import() {
    local tf_resource="$1"
    local aws_resource_id="$2"
    local resource_name="$3"
    
    if [ -z "$aws_resource_id" ] || [ "$aws_resource_id" == "None" ] || [ "$aws_resource_id" == "null" ]; then
        echo "  ⏭️  $resource_name not found, skipping import"
        return 0
    fi
    
    echo "  📥 Importing $resource_name: $aws_resource_id"
    terraform import "$tf_resource" "$aws_resource_id" 2>/dev/null || {
        echo "  ⚠️  Import failed for $resource_name (may already be in state)"
    }
}

# Function to get AWS account ID
get_account_id() {
    aws sts get-caller-identity --query Account --output text 2>/dev/null || echo ""
}

ACCOUNT_ID=$(get_account_id)
REGION=$(aws configure get region 2>/dev/null || echo "us-east-1")

echo "📋 Account ID: $ACCOUNT_ID"
echo "📋 Region: $REGION"
echo ""

# 1. Import DynamoDB Table
echo "🗄️  Checking DynamoDB Tables..."
DYNAMODB_TABLE=$(aws dynamodb describe-table --table-name "${NAME_PREFIX}-comments" --query 'Table.TableName' --output text 2>/dev/null || echo "")
safe_import "aws_dynamodb_table.comments" "$DYNAMODB_TABLE" "DynamoDB Table"

# 2. Import IAM Roles
echo "👤 Checking IAM Roles..."
IAM_ROLE_API=$(aws iam get-role --role-name "${NAME_PREFIX}-lambda-api-role" --query 'Role.RoleName' --output text 2>/dev/null || echo "")
safe_import "aws_iam_role.lambda_api" "$IAM_ROLE_API" "Lambda API IAM Role"

IAM_ROLE_FAKE=$(aws iam get-role --role-name "${NAME_PREFIX}-lambda-fake-pages-role" --query 'Role.RoleName' --output text 2>/dev/null || echo "")
safe_import "aws_iam_role.lambda_fake_pages" "$IAM_ROLE_FAKE" "Lambda Fake Pages IAM Role"

# 3. Import Load Balancers
echo "⚖️  Checking Load Balancers..."
ALB_PUBLIC=$(aws elbv2 describe-load-balancers --names "${NAME_PREFIX}-public-alb" --query 'LoadBalancers[0].LoadBalancerArn' --output text 2>/dev/null || echo "")
safe_import "aws_lb.public" "$ALB_PUBLIC" "Public ALB"

ALB_TIMEOUT=$(aws elbv2 describe-load-balancers --names "${NAME_PREFIX}-timeout-alb" --query 'LoadBalancers[0].LoadBalancerArn' --output text 2>/dev/null || echo "")
safe_import "aws_lb.timeout" "$ALB_TIMEOUT" "Timeout ALB"

# 4. Import Target Groups
echo "🎯 Checking Target Groups..."
TG_LAMBDA=$(aws elbv2 describe-target-groups --names "${NAME_PREFIX}-lambda-tg" --query 'TargetGroups[0].TargetGroupArn' --output text 2>/dev/null || echo "")
safe_import "aws_lb_target_group.lambda" "$TG_LAMBDA" "Lambda Target Group"

# 5. Import CloudWatch Log Groups
echo "📊 Checking CloudWatch Log Groups..."
LOG_GROUP_WAF=$(aws logs describe-log-groups --log-group-name-prefix "aws-waf-logs-${NAME_PREFIX}" --query 'logGroups[0].logGroupName' --output text 2>/dev/null || echo "")
safe_import "aws_cloudwatch_log_group.waf" "$LOG_GROUP_WAF" "WAF Log Group"

LOG_GROUP_API=$(aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/${NAME_PREFIX}-api" --query 'logGroups[0].logGroupName' --output text 2>/dev/null || echo "")
safe_import "aws_cloudwatch_log_group.lambda_api" "$LOG_GROUP_API" "Lambda API Log Group"

LOG_GROUP_FAKE=$(aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/${NAME_PREFIX}-fake-page-generator" --query 'logGroups[0].logGroupName' --output text 2>/dev/null || echo "")
safe_import "aws_cloudwatch_log_group.lambda_fake_page_generator" "$LOG_GROUP_FAKE" "Lambda Fake Pages Log Group"

# 6. Import WAF IP Sets
echo "🛡️  Checking WAF IP Sets..."
IP_SET_ALLOWED=$(aws wafv2 list-ip-sets --scope CLOUDFRONT --query "IPSets[?Name=='${NAME_PREFIX}-allowed-ips'].Id" --output text 2>/dev/null || echo "")
if [ ! -z "$IP_SET_ALLOWED" ] && [ "$IP_SET_ALLOWED" != "None" ]; then
    safe_import "aws_wafv2_ip_set.allowed_ips" "${IP_SET_ALLOWED}/${NAME_PREFIX}-allowed-ips/CLOUDFRONT" "Allowed IPs IP Set"
fi

IP_SET_BLOCKED=$(aws wafv2 list-ip-sets --scope CLOUDFRONT --query "IPSets[?Name=='${NAME_PREFIX}-blocked-ips'].Id" --output text 2>/dev/null || echo "")
if [ ! -z "$IP_SET_BLOCKED" ] && [ "$IP_SET_BLOCKED" != "None" ]; then
    safe_import "aws_wafv2_ip_set.blocked_ips" "${IP_SET_BLOCKED}/${NAME_PREFIX}-blocked-ips/CLOUDFRONT" "Blocked IPs IP Set"
fi

# 7. Import WAF Web ACL
echo "🛡️  Checking WAF Web ACL..."
WEB_ACL=$(aws wafv2 list-web-acls --scope CLOUDFRONT --query "WebACLs[?Name=='${NAME_PREFIX}-web-acl'].Id" --output text 2>/dev/null || echo "")
if [ ! -z "$WEB_ACL" ] && [ "$WEB_ACL" != "None" ]; then
    safe_import "aws_wafv2_web_acl.main" "${WEB_ACL}/${NAME_PREFIX}-web-acl/CLOUDFRONT" "WAF Web ACL"
fi

# 8. Import Lambda Functions
echo "⚡ Checking Lambda Functions..."
LAMBDA_API=$(aws lambda get-function --function-name "${NAME_PREFIX}-api" --query 'Configuration.FunctionName' --output text 2>/dev/null || echo "")
safe_import "aws_lambda_function.api" "$LAMBDA_API" "API Lambda Function"

LAMBDA_FAKE=$(aws lambda get-function --function-name "${NAME_PREFIX}-fake-page-generator" --query 'Configuration.FunctionName' --output text 2>/dev/null || echo "")
safe_import "aws_lambda_function.fake_page_generator" "$LAMBDA_FAKE" "Fake Pages Lambda Function"

# 9. Import S3 Buckets
echo "🪣 Checking S3 Buckets..."
S3_FRONTEND=$(aws s3api list-buckets --query "Buckets[?contains(Name, '${NAME_PREFIX}-frontend')].Name" --output text 2>/dev/null || echo "")
safe_import "aws_s3_bucket.frontend" "$S3_FRONTEND" "Frontend S3 Bucket"

S3_FAKE=$(aws s3api list-buckets --query "Buckets[?contains(Name, '${NAME_PREFIX}-fake-webpages')].Name" --output text 2>/dev/null || echo "")
safe_import "aws_s3_bucket.fake_webpages" "$S3_FAKE" "Fake Webpages S3 Bucket"

# 10. Import VPC and Networking (if they exist)
echo "🌐 Checking VPC Resources..."
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=tag:Name,Values=bot-deception" --query 'Vpcs[0].VpcId' --output text 2>/dev/null || echo "")
safe_import "aws_vpc.main" "$VPC_ID" "Main VPC"

# 11. Import CloudFront Resources (already handled in main script, but adding here for completeness)
echo "☁️  Checking CloudFront Resources..."
CF_OAC_FRONTEND=$(aws cloudfront list-origin-access-controls --query "OriginAccessControlList.Items[?Name=='${NAME_PREFIX}-frontend-oac'].Id" --output text 2>/dev/null || echo "")
safe_import "aws_cloudfront_origin_access_control.frontend" "$CF_OAC_FRONTEND" "Frontend CloudFront OAC"

CF_OAC_FAKE=$(aws cloudfront list-origin-access-controls --query "OriginAccessControlList.Items[?Name=='${NAME_PREFIX}-fake-webpages-oac'].Id" --output text 2>/dev/null || echo "")
safe_import "aws_cloudfront_origin_access_control.fake_webpages" "$CF_OAC_FAKE" "Fake Pages CloudFront OAC"

CF_DISTRIBUTION=$(aws cloudfront list-distributions --query "DistributionList.Items[?Comment=='Bot Deception Demo Distribution'].Id" --output text 2>/dev/null || echo "")
safe_import "aws_cloudfront_distribution.main" "$CF_DISTRIBUTION" "CloudFront Distribution"

echo ""
echo "✅ Resource import scan completed!"
echo "🚀 Proceeding with Terraform plan/apply..."
